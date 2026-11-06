from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.activity_enums import ActivityAction, EntityType
from app.schemas.common import ORMModel, UserBrief


class ActivityLogCreate(BaseModel):
    project_id: int = Field(gt=0)
    task_id: Optional[int] = Field(default=None, gt=0)
    user_id: Optional[int] = Field(default=None, gt=0)
    action: ActivityAction
    entity_type: EntityType
    entity_id: int = Field(gt=0)
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None


class ActivityLogResponse(ORMModel):
    id: int
    project_id: int
    task_id: Optional[int] = None
    user: Optional[UserBrief] = None
    action: str
    entity_type: EntityType
    entity_id: int
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    created_at: datetime


class ActivityLogListResponse(BaseModel):
    items: List[ActivityLogResponse]
    total: int
    page: int
    page_size: int
