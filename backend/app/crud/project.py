import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_invitation import ProjectInvitation
from app.models.list import ListModel
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.schemas.project import ProjectCreate
from app.schemas.project_invitation import InvitationCreate


# ── 1. Hàm dùng chung cho Xoá mềm Project (deleted_at IS NULL) ─────────────
def query_active_projects(db: Session) -> Query:
    """
    Hàm dùng chung trả về Query chỉ lấy các Project chưa bị xoá mềm (deleted_at IS NULL).
    Vì cascade='all, delete-orphan' chỉ có tác dụng khi xoá cứng, mọi truy vấn Project
    đều phải đi qua hàm này để lọc deleted_at IS NULL.
    """
    return db.query(Project).filter(Project.deleted_at.is_(None))


def get_active_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """Lấy dự án đang hoạt động (chưa xoá mềm) theo ID."""
    return query_active_projects(db).filter(Project.id == project_id).first()


# ── 2. Đồng bộ owner_id và dòng owner trong project_members trong 1 transaction ─
def create_project_with_owner(
    db: Session,
    project_in: ProjectCreate,
    owner_id: int,
) -> Project:
    """
    Tạo Project, thêm dòng owner vào project_members và tạo 3 cột mặc định
    trong cùng một transaction để đảm bảo tính toàn vẹn đồng bộ owner.
    """
    if project_in.start_date and project_in.end_date and project_in.end_date < project_in.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày kết thúc không được sớm hơn ngày bắt đầu",
        )

    try:
        project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=owner_id,
            start_date=project_in.start_date,
            end_date=project_in.end_date,
        )
        db.add(project)
        db.flush()  # Lấy project.id trong cùng transaction

        # Đồng bộ owner vào bảng project_members
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner_id,
            role="owner",
        )
        db.add(owner_member)

        # Tạo 3 cột mặc định cho bảng Kanban
        default_lists = [
            ("Cần làm", 0, False),
            ("Đang làm", 1, False),
            ("Hoàn thành", 2, True),
        ]
        for name, pos, is_done in default_lists:
            db.add(
                ListModel(
                    project_id=project.id,
                    name=name,
                    position=pos,
                    is_done_column=is_done,
                )
            )

        db.commit()
        db.refresh(project)
        return project
    except Exception:
        db.rollback()
        raise


def transfer_project_ownership(
    db: Session,
    project: Project,
    owner_member: ProjectMember,
    target_member: ProjectMember,
) -> ProjectMember:
    """
    Chuyển quyền Owner cho thành viên khác: cập nhật đồng thời project.owner_id
    và role trong project_members trong cùng một transaction.
    """
    old_owner_id = owner_member.user_id
    new_owner_id = target_member.user_id
    try:
        owner_member.role = "manager"
        target_member.role = "owner"
        project.owner_id = new_owner_id

        db.add(
            Notification(
                user_id=new_owner_id,
                type="member_role_changed",
                title=f"Bạn đã trở thành Owner của dự án '{project.name}'",
                message=f"Quyền sở hữu dự án '{project.name}' đã được chuyển cho bạn.",
                entity_type="project",
                entity_id=project.id,
                project_id=project.id,
            )
        )
        db.add(
            ActivityLog(
                project_id=project.id,
                user_id=old_owner_id,
                entity_type="project",
                entity_id=project.id,
                action="ownership_transferred",
                old_value=f'{{"owner_id": {old_owner_id}}}',
                new_value=f'{{"owner_id": {new_owner_id}}}',
            )
        )
        db.commit()
        db.refresh(target_member)
        return target_member
    except Exception:
        db.rollback()
        raise


# ── 3. Băm Token lời mời (SHA-256 hex 64 ký tự) & Chống mời trùng trong Service ─
def hash_invitation_token(raw_token: str) -> str:
    """Băm token gốc bằng SHA-256 ra chuỗi hex 64 ký tự để lưu vào cột CHAR(64)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_invitation_token_pair() -> Tuple[str, str]:
    """
    Sinh cặp (raw_token, token_hash):
    - raw_token: gửi qua email cho người nhận.
    - token_hash: bản băm SHA-256 hex (64 ký tự) lưu trong CSDL.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_invitation_token(raw_token)
    return raw_token, token_hash


def create_project_invitation(
    db: Session,
    project: Project,
    inviter_member: ProjectMember,
    invitation_in: InvitationCreate,
) -> Tuple[ProjectInvitation, str]:
    """
    Kiểm tra chống mời trùng trong tầng service (do MySQL không hỗ trợ partial unique index
    chỉ cho trạng thái 'pending') và lưu token dưới dạng SHA-256 hex 64 ký tự.
    Trả về (invitation, raw_token).
    """
    if inviter_member.role == "manager" and invitation_in.role == "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager chỉ có thể mời thành viên với vai trò member hoặc viewer",
        )

    normalized_email = invitation_in.invitee_email.strip().lower()

    # 1. Kiểm tra nếu email đã là thành viên trong dự án
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        is_member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == existing_user.id,
            )
            .first()
        )
        if is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người dùng này đã là thành viên của dự án",
            )

    # 2. Chống mời trùng: Kiểm tra trong service xem đã có lời mời pending cho email này chưa
    now = datetime.utcnow()
    pending_invitations = (
        db.query(ProjectInvitation)
        .filter(
            ProjectInvitation.project_id == project.id,
            ProjectInvitation.invitee_email == normalized_email,
            ProjectInvitation.status == "pending",
        )
        .all()
    )
    for pending_inv in pending_invitations:
        if pending_inv.expires_at > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có lời mời đang chờ phản hồi (pending) cho email này trong dự án",
            )
        else:
            pending_inv.status = "expired"

    # 3. Sinh raw_token (để gửi email) và lưu bản băm SHA-256 hex (64 ký tự) vào DB
    raw_token, token_hash = generate_invitation_token_pair()
    expires_at = now + timedelta(days=7)

    invitation = ProjectInvitation(
        project_id=project.id,
        inviter_id=inviter_member.user_id,
        invitee_email=normalized_email,
        invitee_id=existing_user.id if existing_user else None,
        role=invitation_in.role,
        token=token_hash,
        status="pending",
        expires_at=expires_at,
    )
    db.add(invitation)
    db.flush()

    if existing_user:
        db.add(
            Notification(
                user_id=existing_user.id,
                type="invitation_sent",
                title=f"Lời mời tham gia dự án: {project.name}",
                message=f"Bạn được mời tham gia dự án '{project.name}' với vai trò '{invitation_in.role}'.",
                entity_type="invitation",
                entity_id=invitation.id,
                project_id=project.id,
            )
        )

    db.add(
        ActivityLog(
            project_id=project.id,
            user_id=inviter_member.user_id,
            entity_type="invitation",
            entity_id=invitation.id,
            action="created",
            new_value=f'{{"invitee_email": "{normalized_email}", "role": "{invitation_in.role}"}}',
        )
    )

    db.commit()
    db.refresh(invitation)
    return invitation, raw_token


def find_invitation_by_token(db: Session, token_input: str) -> Optional[ProjectInvitation]:
    """
    Tìm lời mời bằng cách băm SHA-256 token người dùng gửi lên để so khớp với bản băm trong DB.
    Hỗ trợ fallback tìm trực tiếp nếu client truyền sẵn mã băm (ví dụ từ dữ liệu seed).
    """
    token_hash = hash_invitation_token(token_input)
    invitation = db.query(ProjectInvitation).filter(ProjectInvitation.token == token_hash).first()
    if not invitation and len(token_input) == 64:
        invitation = db.query(ProjectInvitation).filter(ProjectInvitation.token == token_input).first()
    return invitation
