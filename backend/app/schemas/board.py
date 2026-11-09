from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

PRIORITIES = {"low", "medium", "high", "urgent"}


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên dự án không được để trống")
        return value


class ProjectCard(ORMModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    role: str


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên danh sách không được để trống")
        return value


class TaskCreate(BaseModel):
    list_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = "medium"

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên công việc không được để trống")
        return value

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: str) -> str:
        if value not in PRIORITIES:
            raise ValueError("Mức ưu tiên không hợp lệ")
        return value


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    list_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Tên công việc không được để trống")
        return value

    @field_validator("priority")
    @classmethod
    def check_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in PRIORITIES:
            raise ValueError("Mức ưu tiên không hợp lệ")
        return value


class TaskCard(ORMModel):
    id: int
    list_id: int
    title: str
    description: Optional[str] = None
    priority: str
    position: int
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BoardList(ORMModel):
    id: int
    name: str
    position: int
    is_done_column: bool
    tasks: list[TaskCard]


class BoardOut(BaseModel):
    project: ProjectCard
    lists: list[BoardList]
