"""CRUD cho bảng tasks.

Điểm đáng chú ý:
- Validate "hạn chót >= ngày bắt đầu" ngay trong CRUD (checker.validate_dates).
- Xoá mềm: đặt is_deleted=True, deleted_at=now() thay vì DELETE khỏi DB.
- Mọi truy vấn đọc đều lọc is_deleted == False, nên task đã xoá "biến mất".
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

NOT_DELETED = Task.is_deleted == False  # noqa: E712  # điều kiện lọc task đã xoá mềm


def validate_dates(start_date: datetime | None, due_date: datetime | None) -> None:
    """Hạn chót phải >= ngày bắt đầu (nếu cả hai được cung cấp)."""
    if start_date and due_date and due_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="Hạn chót (due_date) phải sau hoặc bằng ngày bắt đầu (start_date)",
        )


def get_tasks_by_list(db: Session, list_id: int) -> list[Task]:
    """Task của 1 cột, bỏ qua task đã xoá mềm, sắp theo position."""
    return list(db.scalars(
        select(Task)
        .where(Task.list_id == list_id, NOT_DELETED)
        .order_by(Task.position, Task.id)
    ))


def get_task(db: Session, task_id: int, include_deleted: bool = False) -> Task | None:
    task = db.get(Task, task_id)
    if task is None:
        return None
    if task.is_deleted and not include_deleted:
        return None  # coi như không tồn tại với bên ngoài
    return task


def get_task_or_404(db: Session, task_id: int) -> Task:
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy task id={task_id}")
    return task


def next_position(db: Session, list_id: int) -> int:
    """Position kế tiếp để thêm task nhanh cuối cột."""
    last = db.scalar(
        select(Task.position)
        .where(Task.list_id == list_id, NOT_DELETED)
        .order_by(Task.position.desc())
        .limit(1)
    )
    return (last or 0) + 1


def create_task(db: Session, list_id: int, project_id: int, user_id: int, data: TaskCreate) -> Task:
    validate_dates(data.start_date, data.due_date)
    task = Task(
        **data.model_dump(),
        list_id=list_id,
        project_id=project_id,
        created_by=user_id,
        position=next_position(db, list_id),  # thêm nhanh: luôn cuối cột
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    payload = data.model_dump(exclude_unset=True)
    # Lấy cặp ngày sau khi cập nhật để validate (trường mới > trường cũ)
    start = payload.get("start_date", task.start_date)
    due = payload.get("due_date", task.due_date)
    validate_dates(start, due)
    for field, value in payload.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def soft_delete_task(db: Session, task: Task) -> None:
    """Xoá mềm: chỉ đánh dấu, dữ liệu vẫn nằm trong DB."""
    task.is_deleted = True
    task.deleted_at = datetime.now()
    db.commit()


def restore_task(db: Session, task: Task) -> Task:
    """Kích hoạt lại task đã xoá mềm (tuỳ chọn, tiện kiểm tra)."""
    task.is_deleted = False
    task.deleted_at = None
    db.commit()
    db.refresh(task)
    return task
