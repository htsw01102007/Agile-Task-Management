from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.permissions import get_project_and_membership, require_project_roles
from app.models.project_member import ProjectMember
from app.models.project import Project
from app.models.task import Task, TaskAssignee
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.schemas.project_member import ProjectMemberResponse, MemberUpdateRole

router = APIRouter(prefix="/projects/{project_id}/members", tags=["Members"])


def _unassign_user_from_project_tasks(db: Session, project_id: int, user_id: int) -> None:
    """Gỡ người thực hiện khỏi tất cả các task thuộc dự án khi rời dự án hoặc chuyển thành viewer"""
    task_ids = [
        r[0]
        for r in db.query(Task.id).filter(Task.project_id == project_id).all()
    ]
    if task_ids:
        db.query(TaskAssignee).filter(
            TaskAssignee.task_id.in_(task_ids),
            TaskAssignee.user_id == user_id,
        ).delete(synchronize_session=False)


@router.get("", response_model=List[ProjectMemberResponse])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(get_project_and_membership),
):
    project, _ = data
    members = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at.asc())
        .all()
    )
    return members


@router.patch("/{user_id}", response_model=ProjectMemberResponse)
def update_member_role(
    project_id: int,
    user_id: int,
    role_update: MemberUpdateRole,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, current_member = data

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thành viên không tồn tại")

    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể thay đổi quyền của Owner")

    if current_member.role == "manager" and (member.role == "manager" or role_update.role == "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager không thể thay đổi quyền của Manager khác hoặc cấp quyền Manager",
        )

    old_role = member.role
    member.role = role_update.role

    if role_update.role == "viewer":
        _unassign_user_from_project_tasks(db, project_id, user_id)

    db.add(Notification(
        user_id=user_id,
        type="member_role_changed",
        title=f"Vai trò của bạn trong dự án '{project.name}' đã thay đổi",
        message=f"Vai trò của bạn đã được cập nhật từ '{old_role}' sang '{role_update.role}'.",
        entity_type="member",
        entity_id=user_id,
        project_id=project_id,
    ))
    db.add(ActivityLog(
        project_id=project_id,
        user_id=current_member.user_id,
        entity_type="member",
        entity_id=user_id,
        action="role_changed",
        old_value=f'{{"role": "{old_role}"}}',
        new_value=f'{{"role": "{role_update.role}"}}',
    ))

    db.commit()
    db.refresh(member)
    return member


@router.post("/{user_id}/transfer-ownership", response_model=ProjectMemberResponse)
def transfer_ownership(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner")),
):
    """Chuyển quyền Owner của dự án cho một thành viên khác (Owner cũ trở thành Manager)"""
    project, owner_member = data

    if user_id == owner_member.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bạn đã là Owner của dự án này")

    target_member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not target_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thành viên nhận quyền không tồn tại trong dự án")

    old_owner_id = owner_member.user_id
    owner_member.role = "manager"
    target_member.role = "owner"
    project.owner_id = user_id

    db.add(Notification(
        user_id=user_id,
        type="member_role_changed",
        title=f"Bạn đã trở thành Owner của dự án '{project.name}'",
        message=f"Quyền sở hữu dự án '{project.name}' đã được chuyển cho bạn.",
        entity_type="project",
        entity_id=project_id,
        project_id=project_id,
    ))
    db.add(ActivityLog(
        project_id=project_id,
        user_id=old_owner_id,
        entity_type="project",
        entity_id=project_id,
        action="ownership_transferred",
        old_value=f'{{"owner_id": {old_owner_id}}}',
        new_value=f'{{"owner_id": {user_id}}}',
    ))

    db.commit()
    db.refresh(target_member)
    return target_member


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, current_member = data

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thành viên không tồn tại")

    if member.user_id == current_member.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bạn không thể tự xoá mình khỏi dự án")

    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể xoá Owner khỏi dự án")

    if current_member.role == "manager" and member.role in ["manager", "owner"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager không thể xoá Manager hoặc Owner")

    _unassign_user_from_project_tasks(db, project_id, user_id)
    db.delete(member)

    db.add(Notification(
        user_id=user_id,
        type="member_removed",
        title=f"Bạn đã bị xoá khỏi dự án '{project.name}'",
        message=f"Bạn không còn là thành viên của dự án '{project.name}'.",
        entity_type="project",
        entity_id=project_id,
        project_id=project_id,
    ))
    db.add(ActivityLog(
        project_id=project_id,
        user_id=current_member.user_id,
        entity_type="member",
        entity_id=user_id,
        action="removed",
        old_value=f'{{"user_id": {user_id}, "role": "{member.role}"}}',
        new_value=None,
    ))

    db.commit()
    return None


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_project(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(get_project_and_membership),
):
    project, member = data

    if member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner phải chuyển quyền trước khi rời dự án",
        )

    _unassign_user_from_project_tasks(db, project_id, member.user_id)
    db.delete(member)
    db.add(ActivityLog(
        project_id=project_id,
        user_id=member.user_id,
        entity_type="member",
        entity_id=member.user_id,
        action="left",
        old_value=f'{{"user_id": {member.user_id}, "role": "{member.role}"}}',
        new_value=None,
    ))
    db.commit()
    return None
