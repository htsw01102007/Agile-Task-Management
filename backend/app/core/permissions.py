from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task


def get_project_and_membership(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Project, ProjectMember]:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.deleted_at.is_(None))
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dự án không tồn tại hoặc đã bị xóa",
        )

    # Check membership
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải là thành viên của dự án này",
        )

    return project, member


def require_project_roles(*allowed_roles: str, allow_read_only_when_inactive: bool = False):
    """
    Dependency factory to check if the current user has one of the allowed roles
    in the specified project, and validates if project is active.
    """
    def dependency(
        data: tuple[Project, ProjectMember] = Depends(get_project_and_membership),
    ) -> tuple[Project, ProjectMember]:
        project, member = data

        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Thao tác yêu cầu quyền: {', '.join(allowed_roles)}. Quyền của bạn: {member.role}",
            )

        # If project is completed or archived, modifications are blocked unless specifically allowed
        if not allow_read_only_when_inactive and project.status in ["completed", "archived"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dự án đang ở trạng thái '{project.status}' (chỉ đọc), không thể thực hiện thao tác này",
            )

        return project, member

    return dependency


# ===== TASK PERMISSIONS =====

def get_task_and_membership(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Task, ProjectMember]:
    """Get task and verify user is project member. Task must belong to project and not be soft-deleted."""
    # Verify project membership first
    project, member = get_project_and_membership(project_id, db, current_user)

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id, Task.is_deleted.is_(False))
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công việc không tồn tại hoặc đã bị xóa",
        )

    return task, member


def get_task_with_write_check(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Task, ProjectMember]:
    """Get task and verify user has write permission (not viewer)."""
    task, member = get_task_and_membership(project_id, task_id, db, current_user)

    if member.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer không có quyền chỉnh sửa công việc",
        )

    # Check project status
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )
    if project.status in ["completed", "archived"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dự án đang ở trạng thái '{project.status}' (chỉ đọc), không thể thực hiện thao tác này",
        )

    return task, member


def get_task_for_delete(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Task, ProjectMember]:
    """Get task and verify user can DELETE this task.
    - Owner/Manager: can delete any task
    - Member: can only delete tasks they created
    - Viewer: cannot delete
    """
    task, member = get_task_with_write_check(project_id, task_id, db, current_user)

    if member.role in ["owner", "manager"]:
        return task, member

    # Member: can only delete own created tasks
    if task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn chỉ có thể xoá công việc do chính mình tạo",
        )

    return task, member


def get_task_for_restore(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Task, ProjectMember]:
    """Get soft-deleted task and verify user can RESTORE (owner/manager only)."""
    project, member = get_project_and_membership(project_id, db, current_user)

    if member.role not in ["owner", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Owner hoặc Manager mới có quyền khôi phục công việc đã xoá",
        )

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project_id, Task.is_deleted.is_(True))
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công việc không tồn tại hoặc chưa bị xoá",
        )

    return task, member


def can_assign_task(member: ProjectMember) -> bool:
    """Check if user can assign tasks (not viewer)."""
    return member.role in ["owner", "manager", "member"]


def validate_assignees_not_viewers(
    db: Session,
    project_id: int,
    assignee_ids: list[int],
) -> list[int]:
    """Validate that assignees are project members and not viewers. Returns valid user_ids."""
    if not assignee_ids:
        return []

    # Get project members who are not viewers
    valid_members = (
        db.query(ProjectMember.user_id)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id.in_(assignee_ids),
            ProjectMember.role != "viewer",
        )
        .all()
    )
    valid_user_ids = [m.user_id for m in valid_members]

    invalid_ids = set(assignee_ids) - set(valid_user_ids)
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể giao việc cho user_id: {', '.join(map(str, invalid_ids))} (không phải thành viên hoặc là Viewer)",
        )

    return valid_user_ids
