from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMModel


def _clean_content(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Nội dung mục checklist không được để trống")
    return value


class ChecklistItemCreate(BaseModel):
    content: str = Field(min_length=1, max_length=255)
    position: Optional[int] = Field(default=None, ge=0)

    _content = field_validator("content")(_clean_content)


class ChecklistItemUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_done: Optional[bool] = None

    _content = field_validator("content")(_clean_content)

    @model_validator(mode="after")
    def require_any_field(self) -> "ChecklistItemUpdate":
        if not self.model_fields_set:
            raise ValueError("Cần ít nhất một trường để cập nhật")
        return self


class ChecklistReorder(BaseModel):
    item_ids: List[int] = Field(min_length=1)

    @field_validator("item_ids")
    @classmethod
    def ids_must_be_unique(cls, value: List[int]) -> List[int]:
        if len(set(value)) != len(value):
            raise ValueError("Danh sách id mục checklist bị trùng")
        return value


class ChecklistItemResponse(ORMModel):
    id: int
    task_id: int
    content: str
    position: int
    is_done: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChecklistProgress(BaseModel):
    total: int
    done: int
    percent: float


class ChecklistResponse(BaseModel):
    items: List[ChecklistItemResponse]
    progress: ChecklistProgress

    @classmethod
    def from_items(cls, items) -> "ChecklistResponse":
        total = len(items)
        done = sum(1 for item in items if item.is_done)
        percent = round(done * 100 / total, 1) if total else 0.0
        return cls(
            items=[ChecklistItemResponse.model_validate(item) for item in items],
            progress=ChecklistProgress(total=total, done=done, percent=percent),
        )
