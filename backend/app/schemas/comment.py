from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from app.schemas.common import ORMModel, UserBrief

DELETED_PLACEHOLDER = "Bình luận đã bị xoá"


class CommentContent(BaseModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nội dung bình luận không được để trống")
        return value


class CommentCreate(CommentContent):
    parent_id: Optional[int] = Field(default=None, gt=0)


class CommentUpdate(CommentContent):
    pass


class CommentResponse(ORMModel):
    id: int
    task_id: int
    parent_id: Optional[int] = None
    author: Optional[UserBrief] = None
    content: str
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime
    replies: List["CommentResponse"] = Field(default_factory=list)

    @computed_field
    @property
    def is_edited(self) -> bool:
        return self.edited_at is not None

    @computed_field
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @model_validator(mode="after")
    def mask_deleted_content(self) -> "CommentResponse":
        if self.deleted_at is not None:
            self.content = DELETED_PLACEHOLDER
        return self
