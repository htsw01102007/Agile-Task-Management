"""API CRUD cho lists (cột) trong một project. Đường dẫn: /api/projects/{project_id}/lists

GET    .../lists              danh sách list (cần member trở lên)
POST   .../lists              thêm list        (manager trở lên)
PUT    .../lists/{list_id}    sửa tên/cột hoàn thành (manager trở lên)
PUT    .../lists/reorder      đổi thứ tự theo mảng id   (manager trở lên)
DELETE .../lists/{list_id}    xoá list        (manager trở lên)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import require_role
from app.crud import list as list_crud
from app.db.session import get_db
from app.models.list import ListModel
from app.models.project import Project
from app.schemas.list import ListCreate, ListOut, ListReorder, ListUpdate

router = APIRouter(prefix="/projects/{project_id}/lists", tags=["Lists"])

read_access = require_role("member")   # xem: member trở lên
# thêm/sửa/xoá/đổi thứ tự: manager trở lên
write_access = require_role("manager")


def get_project_or_404(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Không tìm thấy project id={project_id}")
    return project


def get_list_or_404(list_id: int, project_id: int, db: Session = Depends(get_db)) -> ListModel:
    item = list_crud.get_list(db, list_id)
    if item is None or item.project_id != project_id:
        raise HTTPException(
            status_code=404, detail=f"Không tìm thấy list id={list_id}")
    return item


@router.get("", response_model=list[ListOut])
def get_lists(
    project: Project = Depends(get_project_or_404),
    _: object = Depends(read_access),
    db: Session = Depends(get_db),
):
    return list_crud.get_lists(db, project.id)


@router.post("", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(
    data: ListCreate,
    project: Project = Depends(get_project_or_404),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    return list_crud.create_list(db, project.id, data)


@router.put("/reorder", response_model=list[ListOut])
def reorder_lists(
    data: ListReorder,
    project: Project = Depends(get_project_or_404),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    """Đổi thứ tự list: gửi `{"ids": [3, 1, 2]}` theo thứ tự mong muốn."""
    return list_crud.reorder_lists(db, project.id, data.ids)


@router.get("/{list_id}", response_model=ListOut)
def get_list(
    item: ListModel = Depends(get_list_or_404),
    _: object = Depends(read_access),
):
    return item


@router.put("/{list_id}", response_model=ListOut)
def update_list(
    data: ListUpdate,
    item: ListModel = Depends(get_list_or_404),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    return list_crud.update_list(db, item, data)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    item: ListModel = Depends(get_list_or_404),
    _: object = Depends(write_access),
    db: Session = Depends(get_db),
):
    list_crud.delete_list(db, item)
