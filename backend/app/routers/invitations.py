from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.core.permissions import require_project_roles
from app.models.project import Project
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember
from app.crud.project import create_project_invitation
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
    invitation, raw_token = create_project_invitation(
        db=db,
        project=project,
        inviter_member=member,
        invitation_in=invitation_in,
    )
    resp = InvitationResponse.model_validate(invitation)
    resp.raw_token = raw_token
    return resp


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
