"""CRUD cho người thực hiện (task_assignees) + truy vấn việc được giao cho tôi."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.list import ListModel
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task, TaskAssignee
from app.models.user import User


def get_assignees(db: Session, task_id: int) -> list[dict]:
    """Danh sách assignee kèm tên + avatar (để FE vẽ avatar trên thẻ)."""
    rows = db.execute(
        select(TaskAssignee.user_id, User.full_name, User.avatar_url)
        .join(User, User.id == TaskAssignee.user_id)
        .where(TaskAssignee.task_id == task_id)
        .order_by(TaskAssignee.assigned_at)
    ).all()
    return [{"user_id": r[0], "full_name": r[1], "avatar_url": r[2]} for r in rows]


def is_project_member(db: Session, project_id: int, user_id: int) -> bool:
    """Chỉ gán người là THÀNH VIÊN dự án (mọi vai trò, kể cả viewer)."""
    return (
        db.scalar(
            select(ProjectMember.project_id).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        is not None
    )


def assign(db: Session, task: Task, user_id: int) -> TaskAssignee:
    item = TaskAssignee(task_id=task.id, user_id=user_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    # (hook) gọi tạo thông báo khi module thông báo sẵn sàng:
    # notifications.create(db, user_id=user_id, type="task_assigned", task=task)
    return item


def unassign(db: Session, task_id: int, user_id: int) -> bool:
    deleted = (
        db.query(TaskAssignee).filter_by(task_id=task_id, user_id=user_id).delete()
    )
    db.commit()
    return deleted > 0


def get_my_tasks(db: Session, user_id: int) -> list[dict]:
    """Việc được giao cho tôi trên MỌI dự án.

    JOIN: task_assignees -> tasks -> projects, lists (cột chứa task).
    Bỏ qua task đã xoá mềm và project đã lưu trữ.
    """
    rows = db.execute(
        select(
            Task.id,
            Task.title,
            Task.priority,
            Task.due_date,
            Task.completed_at,
            Project.id,
            Project.name,
            ListModel.id,
            ListModel.name,
        )
        .join(TaskAssignee, TaskAssignee.task_id == Task.id)
        .join(Project, Project.id == Task.project_id)
        .outerjoin(ListModel, ListModel.id == Task.list_id)
        .where(
            TaskAssignee.user_id == user_id,
            Task.is_deleted == False,  # noqa: E712
            Project.is_archived == False,  # noqa: E712
        )
        .order_by(Task.due_date.is_(None), Task.due_date, Task.id)
    ).all()
    return [
        {
            "task_id": r[0],
            "title": r[1],
            "priority": r[2],
            "due_date": r[3],
            "completed_at": r[4],
            "project_id": r[5],
            "project_name": r[6],
            "list_id": r[7],
            "list_name": r[8],
        }
        for r in rows
    ]
