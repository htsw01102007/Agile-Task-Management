"""API CRUD cho task trong một list (cột). Đường dẫn: /api/lists/{list_id}/tasks

GET    .../tasks                task trong cột (bỏ qua đã xoá mềm) — member trở lên
POST   .../tasks                thêm nhanh task cuối cột        — manager trở lên
PATCH  .../tasks/{task_id}      sửa (tiêu đề, hạn chót, ưu tiên...) — manager trở lên
DELETE .../tasks/{task_id}      xoá MỀM (đặt deleted_at)        — manager trở lên
POST   .../tasks/{task_id}/restore  khôi phục task đã xoá mềm   — manager trở lên
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_id, require_list_role, require_task_role, require_role
from app.crud import task as task_crud
from app.db.session import get_db
from app.models.list import ListModel
from app.models.task import Task
from app.schemas.task import PaginatedTasks, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(tags=["Tasks"])

list_read_access = require_list_role("member")
list_write_access = require_list_role("manager")
task_write_access = require_task_role("manager")


def get_list_or_404(list_id: int, db: Session = Depends(get_db)) -> ListModel:
    item = db.get(ListModel, list_id)
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Không tìm thấy list id={list_id}")
    return item


def get_task_or_404(task_id: int, db: Session = Depends(get_db)) -> Task:
    task = task_crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=404, detail=f"Không tìm thấy task id={task_id}")
    return task


@router.get("/lists/{list_id}/tasks", response_model=list[TaskOut])
def get_tasks_by_list(
    parent: ListModel = Depends(list_read_access),
    db: Session = Depends(get_db),
):
    return task_crud.get_tasks_by_list(db, parent.id)


@router.get("/lists/{list_id}/tasks/search", response_model=PaginatedTasks)
def search_tasks_in_list(
    parent: ListModel = Depends(list_read_access),
    priority: list[str] | None = Query(default=None, description="low medium high urgent"),
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    assignee_id: int | None = None,
    task_status: str | None = Query(default=None, pattern="^(open|done)$"),
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lọc/tìm task trong 1 cột + phân trang."""
    items, total = task_crud.search_tasks(
        db, list_id=parent.id, priority=priority, due_before=due_before,
        due_after=due_after, assignee_id=assignee_id,
        status_filter=task_status, q=q, page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page,
            "page_size": page_size,
            "total_pages": -(-total // page_size)}


@router.get("/projects/{project_id}/tasks/search", response_model=PaginatedTasks)
def search_tasks_in_project(
    project_id: int = Path(...),
    _: object = Depends(require_role("member")),
    priority: list[str] | None = Query(default=None),
    due_before: datetime | None = None,
    due_after: datetime | None = None,
    assignee_id: int | None = None,
    task_status: str | None = Query(default=None, pattern="^(open|done)$"),
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lọc/tìm task trên TOÀN project (mọi cột) + phân trang."""
    items, total = task_crud.search_tasks(
        db, project_id=project_id, priority=priority,
        due_before=due_before, due_after=due_after, assignee_id=assignee_id,
        status_filter=task_status, q=q, page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page,
            "page_size": page_size,
            "total_pages": -(-total // page_size)}


@router.post("/lists/{list_id}/tasks", response_model=TaskOut,
             status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    parent: ListModel = Depends(list_write_access),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return task_crud.create_task(db, parent.id, parent.project_id, user_id, data)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    data: TaskUpdate,
    task: Task = Depends(get_task_or_404),
    _: object = Depends(task_write_access),
    db: Session = Depends(get_db),
):
    return task_crud.update_task(db, task, data)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_task(
    task: Task = Depends(get_task_or_404),
    _: object = Depends(task_write_access),
    db: Session = Depends(get_db),
):
    task_crud.soft_delete_task(db, task)


@router.post("/tasks/{task_id}/restore", response_model=TaskOut)
def restore_task(
    task_id: int,
    _: object = Depends(task_write_access),
    db: Session = Depends(get_db),
):
    # Task đã xoá mềm vẫn phải "tìm thấy" được để khôi phục
    task = task_crud.get_task(db, task_id, include_deleted=True)
    if task is None or not task.is_deleted:
        raise HTTPException(status_code=404, detail="Task không tồn tại hoặc chưa bị xoá")
    return task_crud.restore_task(db, task)
