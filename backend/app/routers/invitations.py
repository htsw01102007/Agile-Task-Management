from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.permissions import require_project_roles
from app.models.user import User
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.schemas.project_invitation import InvitationCreate, InvitationResponse

router = APIRouter(prefix="/projects/{project_id}/invitations", tags=["Invitations"])


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    project_id: int,
    invitation_in: InvitationCreate,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, member = data

    if member.role == "manager" and invitation_in.role == "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager chỉ có thể mời thành viên với vai trò member hoặc viewer",
        )

    existing_user = db.query(User).filter(User.email == invitation_in.invitee_email).first()
    if existing_user:
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == existing_user.id)
            .first()
        )
        if is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người dùng này đã là thành viên của dự án",
            )

    now = datetime.utcnow()
    pending_inv = (
        db.query(ProjectInvitation)
        .filter(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.invitee_email == invitation_in.invitee_email,
            ProjectInvitation.status == "pending",
        )
        .first()
    )
    if pending_inv:
        if pending_inv.expires_at > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có lời mời đang chờ phản hồi cho email này trong dự án",
            )
        else:
            pending_inv.status = "expired"

    token = secrets.token_hex(32)
    expires_at = now + timedelta(days=7)

    invitation = ProjectInvitation(
        project_id=project_id,
        inviter_id=member.user_id,
        invitee_email=invitation_in.invitee_email,
        invitee_id=existing_user.id if existing_user else None,
        role=invitation_in.role,
        token=token,
        expires_at=expires_at,
    )
    db.add(invitation)
    db.flush()

    if existing_user:
        db.add(Notification(
            user_id=existing_user.id,
            type="invitation_sent",
            title=f"Lời mời tham gia dự án: {project.name}",
            message=f"Bạn được mời tham gia dự án '{project.name}' với vai trò '{invitation_in.role}'.",
            entity_type="invitation",
            entity_id=invitation.id,
            project_id=project_id,
        ))

    db.add(ActivityLog(
        project_id=project_id,
        user_id=member.user_id,
        entity_type="invitation",
        entity_id=invitation.id,
        action="created",
        new_value=f'{{"invitee_email": "{invitation_in.invitee_email}", "role": "{invitation_in.role}"}}',
    ))

    db.commit()
    db.refresh(invitation)
    return invitation


@router.get("", response_model=List[InvitationResponse])
def list_invitations(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, _ = data
    now = datetime.utcnow()
    invitations = (
        db.query(ProjectInvitation)
        .filter(ProjectInvitation.project_id == project_id)
        .order_by(ProjectInvitation.created_at.desc())
        .all()
    )
    updated_expired = False
    for inv in invitations:
        if inv.status == "pending" and inv.expires_at < now:
            inv.status = "expired"
            updated_expired = True
    if updated_expired:
        db.commit()
    return invitations


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_invitation(
    project_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, _ = data
    invitation = (
        db.query(ProjectInvitation)
        .filter(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.status == "pending",
        )
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lời mời không tồn tại hoặc đã được xử lý")

    invitation.status = "cancelled"
    invitation.responded_at = datetime.utcnow()
    db.commit()
    return None
