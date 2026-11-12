"""Schema cho tài nguyên lists (cột công việc trong project)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ListBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Việc cần làm"])
    position: int = Field(default=0, ge=0)
    is_done_column: bool = False


class ListCreate(ListBase):
    """Dữ liệu FE gửi lên khi THÊM mới list."""


class ListUpdate(BaseModel):
    """Sửa list. Trường nào không gửi thì giữ nguyên."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_done_column: bool | None = None


class ListReorder(BaseModel):
    """Đổi thứ tự list: gửi mảng id theo thứ tự mới.
    VD: {"ids": [3, 1, 2]} -> list 3 lên đầu."""
    ids: list[int] = Field(min_length=1)


class ListOut(ListBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
