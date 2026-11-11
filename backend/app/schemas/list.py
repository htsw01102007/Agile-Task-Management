from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ListCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100)
    position: Optional[int] = None
    is_done_column: Optional[bool] = False


class ListUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = None
    is_done_column: Optional[bool] = None


class ListReorder(BaseModel):
    list_ids: List[int] = Field(..., min_length=1, description="Danh sách list_id theo thứ tự mới")


class ListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    position: int
    is_done_column: bool
    created_at: datetime
    updated_at: datetime
