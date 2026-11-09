from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|archived)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ProjectDetailResponse(ProjectResponse):
    model_config = ConfigDict(from_attributes=True)

    member_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    completion_rate: float = 0.0
    user_role: Optional[str] = None
