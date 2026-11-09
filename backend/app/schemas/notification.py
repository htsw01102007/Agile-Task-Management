from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class NotificationCreate(BaseModel):
    user_id: int = Field(..., description="ID người nhận thông báo")
    type: str = Field(default="deadline_reminder", description="Loại thông báo")
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    project_id: Optional[int] = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    project_id: Optional[int] = None
    is_read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    notification_ids: Optional[List[int]] = None  # None = mark all as read


class NotificationUnreadCount(BaseModel):
    unread_count: int


class NotificationBellResponse(BaseModel):
    unread_count: int
    due_soon_created: int = 0
    overdue_created: int = 0
    items: List[NotificationResponse] = []
