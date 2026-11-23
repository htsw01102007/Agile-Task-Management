from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.list import ListResponse
from app.schemas.task import TaskDetailResponse


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
    my_role: Optional[str] = None  # vai trò của tôi trong dự án (owner/manager/member/viewer)
    user_role: Optional[str] = None
    member_count: int = 0
    task_count: int = 0


class ProjectDetailResponse(ProjectResponse):
    model_config = ConfigDict(from_attributes=True)

    completed_task_count: int = 0
    overdue_task_count: int = 0
    completion_rate: float = 0.0


class ProjectDashboardSummaryResponse(BaseModel):
    active_project_count: int = 0
    pending_task_count: int = 0
    completed_task_count: int = 0


class ProjectBoardResponse(BaseModel):
    lists: List[ListResponse] = []
    tasks: List[TaskDetailResponse] = []


class ProjectStatusStat(BaseModel):
    list_id: int
    list_name: str
    is_done_column: bool = False
    task_count: int = 0
    percentage: float = 0.0


class ProjectMemberStat(BaseModel):
    user_id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    role: str
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0


class ProjectOverdueTaskItem(BaseModel):
    id: int
    title: str
    list_id: int
    list_name: str
    priority: str
    due_date: datetime
    assignee_names: List[str] = []


class ProjectStatsResponse(BaseModel):
    project_id: int
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    overdue_tasks: int = 0
    unassigned_tasks: int = 0
    completion_rate: float = 0.0
    by_status: List[ProjectStatusStat] = []
    by_member: List[ProjectMemberStat] = []
    overdue_task_items: List[ProjectOverdueTaskItem] = []
