from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    task_id: Optional[int] = None
    user_id: int
    entity_type: str
    entity_id: Optional[int] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None