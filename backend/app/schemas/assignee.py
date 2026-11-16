"""Schema cho người thực hiện (task_assignees)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssigneeIn(BaseModel):
    """Gán người: FE gửi user_id của thành viên dự án."""

    user_id: int


class AssigneeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    user_id: int
    assigned_at: datetime


class AssigneeBrief(BaseModel):
    """Thông tin gọn của 1 assignee để hiển thị avatar trên thẻ."""

    user_id: int
    full_name: str | None = None
    avatar_url: str | None = None


class MyTaskOut(BaseModel):
    """Một việc được giao cho tôi: thông tin task + project + cột chứa nó."""

    task_id: int
    title: str
    priority: str
    due_date: datetime | None = None
    completed_at: datetime | None = None
    project_id: int
    project_name: str
    list_id: int | None = None
    list_name: str | None = None
