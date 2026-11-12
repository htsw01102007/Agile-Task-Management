"""CRUD cho bảng lists."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.list import ListModel
from app.schemas.list import ListCreate, ListUpdate


def get_lists(db: Session, project_id: int) -> list[ListModel]:
    return list(db.scalars(
        select(ListModel)
        .where(ListModel.project_id == project_id)
        .order_by(ListModel.position, ListModel.id)
    ))


def get_list(db: Session, list_id: int) -> ListModel | None:
    return db.get(ListModel, list_id)


def next_position(db: Session, project_id: int) -> int:
    last = db.scalar(
        select(ListModel.position)
        .where(ListModel.project_id == project_id)
        .order_by(ListModel.position.desc())
        .limit(1)
    )
    return (last or 0) + 1


def create_list(db: Session, project_id: int, data: ListCreate) -> ListModel:
    payload = data.model_dump()
    if payload["position"] == 0:  # FE không truyền position -> đẩy xuống cuối
        payload["position"] = next_position(db, project_id)
    item = ListModel(project_id=project_id, **payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_list(db: Session, item: ListModel, data: ListUpdate) -> ListModel:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def reorder_lists(db: Session, project_id: int, ids: list[int]) -> list[ListModel]:
    """Gán position = chỉ số trong mảng ids (1, 2, 3...)."""
    items = {l.id: l for l in get_lists(db, project_id)}
    for index, list_id in enumerate(ids, start=1):
        if list_id in items:
            items[list_id].position = index
    db.commit()
    return get_lists(db, project_id)


def delete_list(db: Session, item: ListModel) -> None:
    db.delete(item)
    db.commit()
