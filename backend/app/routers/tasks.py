"""Sửa và xoá mềm công việc."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud import board as board_crud
from app.crud.board import BoardError
from app.db.database import get_db
from app.models.entities import User
from app.schemas.board import TaskCard, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _run(action):
    try:
        return action()
    except BoardError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.put("/{task_id}", response_model=TaskCard)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _run(lambda: board_crud.update_task(db, task_id, user.id, data))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _run(lambda: board_crud.soft_delete_task(db, task_id, user.id))
