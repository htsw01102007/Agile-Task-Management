"""Dự án, cột danh sách và công việc trên bảng."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.board import BoardError
from app.crud import board as board_crud
from app.db.database import get_db
from app.models.entities import User
from app.schemas.board import (
    BoardList,
    BoardOut,
    ListCreate,
    ProjectCard,
    ProjectCreate,
    TaskCard,
    TaskCreate,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


def _run(action):
    try:
        return action()
    except BoardError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _project_card(project, role: str) -> ProjectCard:
    return ProjectCard(
        id=project.id,
        name=project.name,
        description=project.description,
        status=str(project.status),
        role=str(role),
    )


@router.get("", response_model=list[ProjectCard])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        _project_card(project, role)
        for project, role in board_crud.list_my_projects(db, user.id)
    ]


@router.post("", response_model=ProjectCard, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project, role = board_crud.create_project(db, user, data)
    return _project_card(project, role)


@router.get("/{project_id}/board", response_model=BoardOut)
def get_board(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    def load():
        project, role, columns = board_crud.get_board(db, project_id, user.id)
        return BoardOut(
            project=_project_card(project, role),
            lists=[
                BoardList(
                    id=column.id,
                    name=column.name,
                    position=column.position,
                    is_done_column=column.is_done_column,
                    tasks=[TaskCard.model_validate(task) for task in column.tasks],
                )
                for column in columns
            ],
        )

    return _run(load)


@router.post("/{project_id}/lists", response_model=BoardList, status_code=201)
def create_list(
    project_id: int,
    data: ListCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    column = _run(lambda: board_crud.create_list(db, project_id, user.id, data))
    return BoardList(
        id=column.id,
        name=column.name,
        position=column.position,
        is_done_column=column.is_done_column,
        tasks=[],
    )


@router.post("/{project_id}/tasks", response_model=TaskCard, status_code=201)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = _run(lambda: board_crud.create_task(db, project_id, user, data))
    return task
