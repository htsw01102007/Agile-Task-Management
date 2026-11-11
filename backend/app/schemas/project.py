from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.list import ListResponse
from app.schemas.task import TaskAssigneeResponse


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


class DashboardSummaryResponse(BaseModel):
    active_project_count: int
    assigned_task_count: int
    pending_task_count: int
    completed_task_count: int


class BoardTaskResponse(BaseModel):
    """Dữ liệu tối thiểu để vẽ một thẻ Kanban, đã nạp sẵn người thực hiện."""
    id: int
    list_id: int
    title: str
    priority: str
    position: int
    created_by: int
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assignees: List[TaskAssigneeResponse] = Field(default_factory=list)


class ProjectBoardResponse(BaseModel):
    """Board được tải theo lô để frontend không phải gọi API cho từng task."""
    lists: List[ListResponse]
    tasks: List[BoardTaskResponse]
