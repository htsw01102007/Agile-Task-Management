from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.permissions import get_project_and_membership, require_project_roles
from app.models.label import Label
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate

router = APIRouter(prefix="/projects/{project_id}/labels", tags=["Labels"])


@router.get("", response_model=List[LabelResponse])
def list_labels(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_project_and_membership),
):
    labels = db.query(Label).filter(Label.project_id == project_id).all()
    return labels


@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    project_id: int,
    label_in: LabelCreate,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager")),
):
    # Check unique name
    existing = db.query(Label).filter(Label.project_id == project_id, Label.name == label_in.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên nhãn đã tồn tại trong dự án")

    label = Label(project_id=project_id, name=label_in.name, color=label_in.color)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


@router.put("/{label_id}", response_model=LabelResponse)
def update_label(
    project_id: int,
    label_id: int,
    label_update: LabelUpdate,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager")),
):
    label = (
        db.query(Label)
        .filter(Label.id == label_id, Label.project_id == project_id)
        .first()
    )
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhãn không tồn tại")

    update_data = label_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != label.name:
        existing = db.query(Label).filter(Label.project_id == project_id, Label.name == update_data["name"]).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên nhãn đã tồn tại trong dự án")

    for field, value in update_data.items():
        setattr(label, field, value)

    db.commit()
    db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(
    project_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager")),
):
    label = (
        db.query(Label)
        .filter(Label.id == label_id, Label.project_id == project_id)
        .first()
    )
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhãn không tồn tại")

    db.delete(label)
    db.commit()
    return None
