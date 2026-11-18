"""Đọc và ghi dự án, danh sách, công việc cho bảng kanban."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Project, Task, TaskList, User
from app.models.project_member import ProjectMember
from app.schemas.board import ListCreate, ProjectCreate, TaskCreate, TaskUpdate

WRITE_ROLES = {"owner", "manager", "member"}


class BoardError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def list_my_projects(db: Session, user_id: int) -> list[tuple[Project, str]]:
    rows = db.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id, Project.deleted_at.is_(None))
        .order_by(Project.id.desc())
    ).all()
    return [(project, role) for project, role in rows]


def create_project(db: Session, user: User, data: ProjectCreate) -> tuple[Project, str]:
    project = Project(name=data.name, description=data.description, owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
    for position, name, done in (
        (1, "Cần làm", False),
        (2, "Đang làm", False),
        (3, "Hoàn thành", True),
    ):
        db.add(
            TaskList(
                project_id=project.id,
                name=name,
                position=position,
                is_done_column=done,
            )
        )
    db.commit()
    db.refresh(project)
    return project, "owner"


def membership(db: Session, project_id: int, user_id: int) -> tuple[Project, ProjectMember]:
    project = db.get(Project, project_id)
    if project is None or project.deleted_at is not None:
        raise BoardError(404, "Không tìm thấy dự án")
    member = db.get(ProjectMember, (project_id, user_id))
    if member is None:
        raise BoardError(403, "Bạn không phải thành viên của dự án")
    return project, member


def require_writer(db: Session, project_id: int, user_id: int) -> tuple[Project, ProjectMember]:
    project, member = membership(db, project_id, user_id)
    if str(project.status) != "active":
        raise BoardError(403, "Dự án đang ở chế độ chỉ đọc")
    if member.role not in WRITE_ROLES:
        raise BoardError(403, "Bạn không có quyền sửa dự án này")
    return project, member


def get_board(db: Session, project_id: int, user_id: int) -> tuple[Project, str, list[TaskList]]:
    project, member = membership(db, project_id, user_id)
    lists = list(
        db.scalars(
            select(TaskList)
            .where(TaskList.project_id == project.id)
            .order_by(TaskList.position, TaskList.id)
        )
    )
    tasks = list(
        db.scalars(
            select(Task)
            .where(Task.project_id == project.id, Task.deleted_at.is_(None))
            .order_by(Task.position, Task.id)
        )
    )
    grouped: dict[int, list[Task]] = {item.id: [] for item in lists}
    for task in tasks:
        grouped.setdefault(task.list_id, []).append(task)
    for item in lists:
        item.tasks = grouped.get(item.id, [])
    return project, member.role, lists


def create_list(db: Session, project_id: int, user_id: int, data: ListCreate) -> TaskList:
    project, _member = require_writer(db, project_id, user_id)
    position = db.scalar(
        select(func.coalesce(func.max(TaskList.position), 0)).where(
            TaskList.project_id == project.id
        )
    )
    item = TaskList(project_id=project.id, name=data.name, position=int(position) + 1)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _list_in_project(db: Session, project_id: int, list_id: int) -> TaskList:
    item = db.get(TaskList, list_id)
    if item is None or item.project_id != project_id:
        raise BoardError(404, "Không tìm thấy danh sách")
    return item


def create_task(db: Session, project_id: int, user: User, data: TaskCreate) -> Task:
    project, _member = require_writer(db, project_id, user.id)
    column = _list_in_project(db, project.id, data.list_id)
    position = db.scalar(
        select(func.coalesce(func.max(Task.position), 0)).where(
            Task.list_id == column.id, Task.deleted_at.is_(None)
        )
    )
    task = Task(
        project_id=project.id,
        list_id=column.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        position=int(position) + 1,
        created_by=user.id,
        completed_at=datetime.now() if column.is_done_column else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_for_user(db: Session, task_id: int, user_id: int, *, write: bool) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.deleted_at is not None:
        raise BoardError(404, "Không tìm thấy công việc")
    if write:
        require_writer(db, task.project_id, user_id)
    else:
        membership(db, task.project_id, user_id)
    return task


def update_task(db: Session, task_id: int, user_id: int, data: TaskUpdate) -> Task:
    task = get_task_for_user(db, task_id, user_id, write=True)
    changes = data.model_dump(exclude_unset=True)
    if "list_id" in changes:
        column = _list_in_project(db, task.project_id, changes["list_id"])
        task.list_id = column.id
        task.completed_at = datetime.now() if column.is_done_column else None
    if "title" in changes:
        task.title = changes["title"]
    if "description" in changes:
        task.description = changes["description"]
    if "priority" in changes:
        task.priority = changes["priority"]
    db.commit()
    db.refresh(task)
    return task


def soft_delete_task(db: Session, task_id: int, user_id: int) -> None:
    task = get_task_for_user(db, task_id, user_id, write=True)
    task.deleted_at = datetime.now()
    db.commit()
