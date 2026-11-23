import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.ws_manager import notify_user_sync
from app.models.user import User
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.crud.project import find_invitation_by_token, get_active_project_by_id
from app.schemas.project_invitation import InvitationResponse

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.get("/me", response_model=List[InvitationResponse])
def list_my_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách các lời mời tham gia dự án gửi tới email của người dùng hiện tại"""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    invitations = (
        db.query(ProjectInvitation)
        .join(Project, Project.id == ProjectInvitation.project_id)
        .filter(
            func.lower(ProjectInvitation.invitee_email) == current_user.email.lower(),
            Project.deleted_at.is_(None),
        )
        .order_by(ProjectInvitation.created_at.desc())
        .all()
    )
    changed = False
    for inv in invitations:
        if inv.status == "pending" and inv.expires_at < now:
            inv.status = "expired"
            changed = True
    if changed:
        db.commit()
    return invitations


@router.post("/accept/{token}")
def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = find_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lời mời không tồn tại")
    # Khoá dòng lời mời: 2 request chấp nhận đồng thời sẽ được xử lý tuần tự
    invitation = (
        db.query(ProjectInvitation)
        .filter(ProjectInvitation.id == invitation.id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời không còn hiệu lực")
    if invitation.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        invitation.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời đã hết hạn")

    project = get_active_project_by_id(db, invitation.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dự án không tồn tại hoặc đã bị xoá")
    if project.status in ("completed", "archived"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dự án đang ở trạng thái '{project.status}' (chỉ đọc), không thể chấp nhận lời mời lúc này",
        )

    if invitation.invitee_email.lower() != current_user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lời mời này không dành cho bạn")

    existing_member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == invitation.project_id, ProjectMember.user_id == current_user.id)
        .first()
    )
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bạn đã là thành viên của dự án")

    member = ProjectMember(
        project_id=invitation.project_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(member)

    invitation.status = "accepted"
    invitation.invitee_id = current_user.id
    invitation.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    notif = None
    if invitation.inviter_id is not None:
        notif = Notification(
            user_id=invitation.inviter_id,
            type="invitation_accepted",
            title=f"{current_user.full_name} đã chấp nhận lời mời",
            message=f"{current_user.full_name} ({current_user.email}) đã tham gia dự án '{project.name}'.",
            entity_type="invitation",
            entity_id=invitation.id,
            project_id=invitation.project_id,
        )
        db.add(notif)
    db.add(
        ActivityLog(
            project_id=invitation.project_id,
            user_id=current_user.id,
            entity_type="member",
            entity_id=current_user.id,
            action="joined",
            new_value=json.dumps({"user_id": current_user.id, "role": invitation.role}, ensure_ascii=False),
        )
    )

    try:
        db.commit()
    except IntegrityError:
        # Thêm project_members và cập nhật lời mời nằm trong cùng transaction -> rollback cả hai
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bạn đã là thành viên của dự án")

    if invitation.inviter_id is not None and notif is not None:
        db.refresh(notif)
        notify_user_sync(
            invitation.inviter_id,
            "notification_created",
            {
                "id": notif.id,
                "type": notif.type,
                "title": notif.title,
                "message": notif.message,
                "entity_type": notif.entity_type,
                "entity_id": notif.entity_id,
                "project_id": notif.project_id,
            },
        )
    return {
        "message": "Đã chấp nhận lời mời tham gia dự án",
        "project_id": invitation.project_id,
    }


@router.post("/decline/{token}")
def decline_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = find_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lời mời không tồn tại")
    if invitation.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời không còn hiệu lực")
    if invitation.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        invitation.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lời mời đã hết hạn")
    if invitation.invitee_email.lower() != current_user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lời mời này không dành cho bạn")

    project = get_active_project_by_id(db, invitation.project_id)

    invitation.status = "declined"
    invitation.invitee_id = current_user.id
    invitation.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    notif = None
    if invitation.inviter_id is not None:
        notif = Notification(
            user_id=invitation.inviter_id,
            type="invitation_declined",
            title=f"{current_user.full_name} đã từ chối lời mời",
            message=f"{current_user.full_name} ({current_user.email}) đã từ chối lời mời vào dự án '{project.name if project else invitation.project_id}'.",
            entity_type="invitation",
            entity_id=invitation.id,
            project_id=invitation.project_id,
        )
        db.add(notif)

    db.commit()
    if invitation.inviter_id is not None and notif is not None:
        db.refresh(notif)
        notify_user_sync(
            invitation.inviter_id,
            "notification_created",
            {
                "id": notif.id,
                "type": notif.type,
                "title": notif.title,
                "message": notif.message,
                "entity_type": notif.entity_type,
                "entity_id": notif.entity_id,
                "project_id": notif.project_id,
            },
        )
    return {"message": "Đã từ chối lời mời tham gia dự án"}
