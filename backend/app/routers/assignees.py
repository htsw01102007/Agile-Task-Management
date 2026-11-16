"""API người thực hiện (assignees) + việc được giao cho tôi.

PUT    /api/tasks/{task_id}/assignees   gán người (member của dự án) — manager+
DELETE /api/tasks/{task_id}/assignees/{user_id}  bỏ gán — manager+
GET    /api/tasks/{task_id}/assignees   xem danh sách — member+
GET    /api/my-tasks                    việc được giao cho tôi trên mọi dự án
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.permissions import get_current_user_id, require_task_role
from app.crud import assignee as assignee_crud
from app.db.session import get_db
from app.models.task import Task
from app.schemas.assignee import AssigneeBrief, AssigneeIn, MyTaskOut

router = APIRouter(tags=["Assignees"])

read_access = require_task_role("member")
write_access = require_task_role("manager")


def get_task_or_404(task_id: int, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy task id={task_id}")
    return task


@router.get("/tasks/{task_id}/assignees", response_model=list[AssigneeBrief])
def list_assignees(
    task: Task = Depends(get_task_or_404),
    _: object = Depends(read_access),
    db: Session = Depends(get_db),
):
    return assignee_crud.get_assignees(db, task.id)


@router.put("/tasks/{task_id}/assignees", status_code=status.HTTP_201_CREATED)
def assign_user(
    data: AssigneeIn,
    task: Task = Depends(get_task_or_404),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    """Gán người thực hiện. Người được gán PHẢI là thành viên dự án."""
    if not assignee_crud.is_project_member(db, task.project_id, data.user_id):
        raise HTTPException(
            status_code=422,
            detail="Người được gán phải là thành viên của dự án",
        )
    existing = assignee_crud.get_assignees(db, task.id)
    if any(a["user_id"] == data.user_id for a in existing):
        raise HTTPException(status_code=409, detail="Người này đã được gán cho task")
    item = assignee_crud.assign(db, task, data.user_id)
    # TODO(giai doan sau): notifications.create(...) khi module thong bao san sang:
    # thong bao cho nguoi duoc gan: "Bạn được giao việc <title>"
    return {
        "task_id": item.task_id,
        "user_id": item.user_id,
        "assigned_at": item.assigned_at,
    }


@router.delete(
    "/tasks/{task_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def unassign_user(
    task: Task = Depends(get_task_or_404),
    user_id: int = Path(...),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    if not assignee_crud.unassign(db, task.id, user_id):
        raise HTTPException(status_code=404, detail="Người này chưa được gán")


@router.get("/my-tasks", response_model=list[MyTaskOut])
def my_tasks(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Việc được giao cho tôi trên MỌI dự án (JOIN tasks, lists, projects)."""
    return assignee_crud.get_my_tasks(db, user_id)
