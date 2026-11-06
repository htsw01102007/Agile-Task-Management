import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMModel

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _clean_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Tên nhãn không được để trống")
    return value


def _clean_color(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not HEX_COLOR_PATTERN.match(value):
        raise ValueError("Mã màu phải có dạng #RRGGBB")
    return value.upper()


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=7, max_length=7)

    _name = field_validator("name")(_clean_name)
    _color = field_validator("color")(_clean_color)


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, min_length=7, max_length=7)

    _name = field_validator("name")(_clean_name)
    _color = field_validator("color")(_clean_color)

    @model_validator(mode="after")
    def require_any_field(self) -> "LabelUpdate":
        if not self.model_fields_set:
            raise ValueError("Cần ít nhất một trường để cập nhật")
        return self


class LabelBrief(ORMModel):
    id: int
    name: str
    color: str


class LabelResponse(LabelBrief):
    project_id: int
    created_at: datetime
    updated_at: datetime


class TaskLabelAttach(BaseModel):
    label_id: int = Field(gt=0)


class TaskLabelResponse(ORMModel):
    task_id: int
    label_id: int
    created_at: datetime
