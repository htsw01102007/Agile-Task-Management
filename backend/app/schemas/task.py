"""Schema cho tài nguyên tasks (thẻ công việc trong 1 cột)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=500, examples=["Làm giao diện login"])
    description: str | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    start_date: datetime | None = None
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    """Dữ liệu FE gửi lên khi THÊM mới task vào 1 list."""


class TaskUpdate(BaseModel):
    """Sửa task. Trường nào không gửi thì giữ nguyên."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high|urgent)$")
    position: int | None = Field(default=None, ge=0)
    start_date: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    list_id: int
    position: int
    completed_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
