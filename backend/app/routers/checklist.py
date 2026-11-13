from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.permissions import get_task_and_membership, get_task_with_write_check
from app.core.ws_manager import notify_project_sync
from app.models.checklist import ChecklistItem
from app.schemas.checklist import (
    ChecklistItemCreate,
    ChecklistItemUpdate,
    ChecklistReorder,
    ChecklistItemResponse,
    ChecklistSummaryResponse,
)

router = APIRouter(prefix="/projects/{project_id}/tasks/{task_id}/checklist", tags=["Checklist"])


def _renumber_checklist(db: Session, task_id: int) -> List[ChecklistItem]:
    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.task_id == task_id)
        .order_by(ChecklistItem.position.asc(), ChecklistItem.id.asc())
        .all()
    )
    for idx, item in enumerate(items):
        item.position = idx
    return items


@router.get("", response_model=List[ChecklistItemResponse])
def list_checklist_items(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_and_membership),
):
    """Danh sách checklist items của task"""
    task, member = data
    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.task_id == task_id)
        .order_by(ChecklistItem.position.asc(), ChecklistItem.id.asc())
        .all()
    )
    return items


@router.get("/summary", response_model=ChecklistSummaryResponse)
def get_checklist_summary(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_and_membership),
):
    """Lấy danh sách checklist kèm tiến độ hoàn thành (%)"""
    task, member = data
    items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.task_id == task_id)
        .order_by(ChecklistItem.position.asc(), ChecklistItem.id.asc())
        .all()
    )
    total = len(items)
    completed = sum(1 for item in items if item.is_done)
    progress = round((completed / total) * 100, 2) if total > 0 else 0.0
    return ChecklistSummaryResponse(
        total_items=total,
        completed_items=completed,
        progress_percent=progress,
        items=[ChecklistItemResponse.model_validate(i) for i in items],
    )


@router.post("", response_model=ChecklistItemResponse, status_code=status.HTTP_201_CREATED)
def create_checklist_item(
    project_id: int,
    task_id: int,
    item_in: ChecklistItemCreate,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Tạo checklist item mới"""
    task, member = data

    max_pos = (
        db.query(ChecklistItem.position)
        .filter(ChecklistItem.task_id == task_id)
        .order_by(ChecklistItem.position.desc())
        .first()
    )
    position = item_in.position if item_in.position is not None else ((max_pos[0] + 1) if max_pos else 0)

    item = ChecklistItem(
        task_id=task_id,
        content=item_in.content,
        position=position,
    )
    db.add(item)
    db.flush()
    _renumber_checklist(db, task_id)
    db.commit()
    db.refresh(item)

    notify_project_sync(
        project_id,
        "checklist_updated",
        {"task_id": task_id, "action": "created", "item_id": item.id},
    )
    return item


@router.patch("/reorder", response_model=List[ChecklistItemResponse])
def reorder_checklist_items(
    project_id: int,
    task_id: int,
    reorder_in: ChecklistReorder,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Sắp xếp lại thứ tự các checklist item trong task"""
    task, member = data

    items = db.query(ChecklistItem).filter(ChecklistItem.task_id == task_id).all()
    item_map = {item.id: item for item in items}

    if len(reorder_in.item_ids) != len(items) or set(reorder_in.item_ids) != set(item_map.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách item_ids phải chứa đầy đủ tất cả checklist items của công việc này",
        )

    for idx, iid in enumerate(reorder_in.item_ids):
        item_map[iid].position = idx

    db.commit()
    ordered = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.task_id == task_id)
        .order_by(ChecklistItem.position.asc())
        .all()
    )
    notify_project_sync(
        project_id,
        "checklist_updated",
        {"task_id": task_id, "action": "reordered", "item_ids": reorder_in.item_ids},
    )
    return ordered


@router.put("/{item_id}", response_model=ChecklistItemResponse)
def update_checklist_item(
    project_id: int,
    task_id: int,
    item_id: int,
    item_update: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Cập nhật checklist item (nội dung, trạng thái is_done, vị trí position)"""
    task, member = data

    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id, ChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item không tồn tại")

    update_data = item_update.model_dump(exclude_unset=True)
    if "content" in update_data and update_data["content"] is not None:
        item.content = update_data["content"]
    if "is_done" in update_data and update_data["is_done"] is not None:
        item.is_done = update_data["is_done"]
    if "position" in update_data and update_data["position"] is not None:
        others = (
            db.query(ChecklistItem)
            .filter(ChecklistItem.task_id == task_id, ChecklistItem.id != item_id)
            .order_by(ChecklistItem.position.asc(), ChecklistItem.id.asc())
            .all()
        )
        new_pos = max(0, min(update_data["position"], len(others)))
        others.insert(new_pos, item)
        for idx, i in enumerate(others):
            i.position = idx

    db.commit()
    db.refresh(item)

    notify_project_sync(
        project_id,
        "checklist_updated",
        {"task_id": task_id, "action": "updated", "item_id": item.id, "is_done": item.is_done},
    )
    return item


@router.patch("/{item_id}/toggle", response_model=ChecklistItemResponse)
def toggle_checklist_item(
    project_id: int,
    task_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Đánh dấu hoàn thành / bỏ hoàn thành nhanh một mục checklist"""
    task, member = data

    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id, ChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item không tồn tại")

    item.is_done = not item.is_done
    db.commit()
    db.refresh(item)

    notify_project_sync(
        project_id,
        "checklist_updated",
        {"task_id": task_id, "action": "toggled", "item_id": item.id, "is_done": item.is_done},
    )
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist_item(
    project_id: int,
    task_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Xoá checklist item và đánh số lại thứ tự"""
    task, member = data

    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id, ChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item không tồn tại")

    db.delete(item)
    db.flush()
    _renumber_checklist(db, task_id)
    db.commit()

    notify_project_sync(
        project_id,
        "checklist_updated",
        {"task_id": task_id, "action": "deleted", "item_id": item_id},
    )
    return None
