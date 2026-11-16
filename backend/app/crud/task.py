"""CRUD cho bảng tasks.

Điểm đáng chú ý:
- Validate "hạn chót >= ngày bắt đầu" ngay trong CRUD (checker.validate_dates).
- Xoá mềm: đặt is_deleted=True, deleted_at=now() thay vì DELETE khỏi DB.
- Mọi truy vấn đọc đều lọc is_deleted == False, nên task đã xoá "biến mất".
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from app.models.project_member import ProjectMember
from app.models.task import Task, TaskAssignee
from app.schemas.task import TaskCreate, TaskUpdate

NOT_DELETED = Task.is_deleted == False  # noqa: E712  # điều kiện lọc task đã xoá mềm


def validate_dates(start_date: datetime | None, due_date: datetime | None) -> None:
    """Hạn chót phải >= ngày bắt đầu (nếu cả hai được cung cấp)."""
    if start_date and due_date and due_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="Hạn chót (due_date) phải sau hoặc bằng ngày bắt đầu (start_date)",
        )


def build_task_filters(
    *,
    priority: list[str] | None = None,
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    assignee_id: int | None = None,
    status_filter: str | None = None,
    q: str | None = None,
):
    """Dựng điều kiện WHERE dùng chung cho mọi endpoint lọc task.

    - priority: 1 hoặc nhiều giá trị (low/medium/high/urgent)
    - due_before / due_after: lọc theo hạn chót
    - assignee_id: chỉ task có người này thực hiện
    - status: "open" (chưa hoàn thành) | "done" (đã có completed_at) | mặc định tất cả
    - q: tìm theo từ khoá trong tiêu đề + mô tả
    Trả về (conditions, cần JOIN assignees hay không).
    """
    conds = [NOT_DELETED]
    join_assignees = False
    if priority:
        conds.append(Task.priority.in_(priority))
    if due_before:
        conds.append(Task.due_date <= due_before)
    if due_after:
        conds.append(Task.due_date >= due_after)
    if assignee_id is not None:
        conds.append(TaskAssignee.user_id == assignee_id)
        join_assignees = True
    if status_filter == "open":
        conds.append(Task.completed_at.is_(None))
    elif status_filter == "done":
        conds.append(Task.completed_at.is_not(None))
    if q:
        keyword = f"%{q}%"
        conds.append(Task.title.ilike(keyword) | Task.description.ilike(keyword))
    return conds, join_assignees


def search_tasks(
    db: Session,
    *,
    project_id: int | None = None,
    list_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    **filters,
) -> tuple[list[Task], int]:
    """Lọc + tìm + phân trang task. Trả về (danh sách, tổng số khớp).

    Ít nhất một trong project_id / list_id phải có để xác định phạm vi.
    """
    conds, join_assignees = build_task_filters(**filters)
    if project_id is not None:
        conds.append(Task.project_id == project_id)
    if list_id is not None:
        conds.append(Task.list_id == list_id)

    query = select(Task)
    if join_assignees:
        query = query.join(TaskAssignee, TaskAssignee.task_id == Task.id)
    query = query.where(*conds)

    total = db.scalar(select(sa_func.count()).select_from(query.subquery()))
    page = max(1, page)
    page_size = min(max(1, page_size), 100)  # chặn page_size quá lớn
    items = db.scalars(
        query.order_by(Task.position, Task.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return list(items), total


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
