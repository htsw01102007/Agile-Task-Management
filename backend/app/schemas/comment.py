from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(..., min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(..., min_length=1, max_length=5000)


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