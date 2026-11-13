from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ChecklistItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(..., min_length=1, max_length=500)
    position: Optional[int] = None


class ChecklistItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: Optional[str] = Field(None, min_length=1, max_length=500)
    is_done: Optional[bool] = None
    position: Optional[int] = None


class ChecklistReorder(BaseModel):
    item_ids: List[int] = Field(..., min_length=1, description="Danh sách id của checklist item theo thứ tự mới")


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    content: str
    is_done: bool
    position: int
    created_at: datetime
    updated_at: datetime


class ChecklistSummaryResponse(BaseModel):
    total_items: int
    completed_items: int
    progress_percent: float
    items: List[ChecklistItemResponse]
