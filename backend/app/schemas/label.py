from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LabelCreate(BaseModel):
    name: str = Field(..., max_length=50)
    color: str = Field("#808080", pattern="^#[0-9a-fA-F]{6}$")


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9a-fA-F]{6}$")


class LabelResponse(BaseModel):
    id: int
    project_id: int
    name: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True
