from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    list_id: int = Field(..., description="ID của list (column) chứa task")
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    position: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assignee_ids: Optional[List[int]] = Field(default_factory=list, description="Danh sách user_id giao việc")
    label_ids: Optional[List[int]] = Field(default_factory=list, description="Danh sách label_id")


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    position: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    list_id: Optional[int] = None  # For moving task between lists


class TaskMove(BaseModel):
    """Move task to another list with position"""
    list_id: int = Field(..., description="ID list đích")
    position: int = Field(default=0, ge=0, description="Vị trí trong list đích")


class TaskReorder(BaseModel):
    """Reorder multiple tasks within a list"""
    task_ids: List[int] = Field(..., min_length=1, description="Danh sách task_id theo thứ tự mới")


class TaskAssigneeAssignRequest(BaseModel):
    """Giao việc cho một hoặc nhiều thành viên"""
    user_id: Optional[int] = Field(None, description="ID của một thành viên")
    user_ids: Optional[List[int]] = Field(None, description="Danh sách ID thành viên")


class TaskLabelAttachRequest(BaseModel):
    """Gắn một hoặc nhiều nhãn vào task"""
    label_id: Optional[int] = Field(None, description="ID của một nhãn")
    label_ids: Optional[List[int]] = Field(None, description="Danh sách ID nhãn")


class TaskAssigneeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    assigned_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None


class TaskLabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label_id: int
    label_name: str
    label_color: str


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    content: str
    is_done: bool
    position: int
    created_at: datetime
    updated_at: datetime


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    list_id: int
    title: str
    description: Optional[str]
    priority: str
    position: int
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskResponse):
    """Task với đầy đủ quan hệ và tiến độ checklist"""
    assignees: List[TaskAssigneeResponse] = []
    labels: List[TaskLabelResponse] = []
    checklist_items: List[ChecklistItemResponse] = []
    checklist_total: int = 0
    checklist_completed: int = 0
    checklist_progress: float = 0.0
    comments_count: int = 0
    attachments_count: int = 0
    creator_name: Optional[str] = None


class MyTaskFilter(BaseModel):
    """Filter cho API /my-tasks"""
    project_id: Optional[int] = None
    list_id: Optional[int] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    is_completed: Optional[bool] = None
    is_overdue: Optional[bool] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    search: Optional[str] = None
    label_ids: Optional[str] = None  # comma-separated
    sort_by: str = Field(default="due_date", pattern="^(due_date|priority|created_at|position)$")
    order: str = Field(default="asc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
