from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MemberUpdateRole(BaseModel):
    role: str = Field(..., pattern="^(manager|member|viewer)$")


class UserBasicInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    is_active: bool = True


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: Optional[UserBasicInfo] = None
