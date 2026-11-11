from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.auth import StrongPassword


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    system_role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: str = Field(min_length=1, max_length=150)
    password: StrongPassword


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1, max_length=150)


class AdminDashboardResponse(BaseModel):
    user_count: int
    active_user_count: int
    project_count: int
    active_project_count: int
    task_count: int
    completed_task_count: int
    recent_users: list[AdminUserResponse]
