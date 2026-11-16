"""CRUD cho bảng lists."""
from datetime import datetime

from sqlalchemy import delete as sa_delete, false as sa_false, select, update as sa_update
from sqlalchemy.orm import Session

from app.crud.task import NOT_DELETED
from app.models.list import ListModel
from app.models.task import Task
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
    items = {lst.id: lst for lst in get_lists(db, project_id)}
    for index, list_id in enumerate(ids, start=1):
        if list_id in items:
            items[list_id].position = index
    db.commit()
    return get_lists(db, project_id)


def set_done_column(db: Session, item: ListModel, is_done: bool) -> ListModel:
    """Đánh dấu cột hoàn thành. Mỗi project chỉ có TỐI ĐA 1 cột hoàn thành:
    nếu đánh dấu list này thì bỏ cờ ở list khác."""
    if is_done:
        others = db.scalars(
            select(ListModel).where(
                ListModel.project_id == item.project_id,
                ListModel.id != item.id,
                ListModel.is_done_column == True,  # noqa: E712
            )
        )
        for other in others:
            other.is_done_column = False
    item.is_done_column = is_done
    db.commit()
    db.refresh(item)
    return item


def soft_delete_list(db: Session, item: ListModel) -> int:
    """Xoá mềm toàn bộ task trong list rồi xoá list — trong MỘT transaction.

    Dùng SQL UPDATE/DELETE trực tiếp (không qua ORM cascade) để task KHÔNG
    bị xoá cứng bởi relationship cascade="all, delete-orphan" của ListModel.
    Lỗi giữa chừng -> rollback toàn bộ, dữ liệu nguyên vẹn."""
    now = datetime.now()
    try:
        # 1) Xoá mềm mọi task chưa bị xoá của list này (trước khi xoá list,
        #    vì FK tasks.list_id ON DELETE CASCADE sẽ xoá cứng task nếu chậm tay)
        task_ids = db.scalars(
            select(Task.id).where(Task.list_id == item.id, NOT_DELETED)
        ).all()
        if task_ids:
            db.query(Task).filter(Task.id.in_(task_ids)).update(
                {Task.is_deleted: True, Task.deleted_at: now},
                synchronize_session=False,
            )
            db.flush()  # đẩy UPDATE xuống DB trong cùng transaction
        # 2) Trước khi xoá list: chuyển task sang "không thuộc list" bằng cách
        #    NULL hoá list_id — nhưng cột đang NOT NULL + FK CASCADE nên ta tắt
        #    cascade ở mức DB một lần khi migration (xem sql/init.sql) và để
        #    task đã xoá mềm tồn tại độc lập bằng list_id = NULL.
        db.execute(
            sa_update(Task)
            .where(Task.id.in_(task_ids) if task_ids else sa_false())
            .values(list_id=None)
        )
        db.execute(sa_delete(ListModel).where(ListModel.id == item.id))
        # 3) Cập nhật lại position 1,2,3... cho các list còn lại
        remaining = db.scalars(
            select(ListModel)
            .where(ListModel.project_id == item.project_id)
            .order_by(ListModel.position, ListModel.id)
        ).all()
        for index, lst in enumerate(remaining, start=1):
            lst.position = index
        db.commit()
        return len(task_ids)
    except Exception:
        db.rollback()
        raise


def delete_list(db: Session, item: ListModel) -> None:
    db.delete(item)
    db.commit()
