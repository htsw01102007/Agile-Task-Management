"""Pydantic schemas for the sample items CRUD API."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, examples=["Cơm rang"])
    description: str | None = Field(default=None, examples=["Mô tả ngắn"])
    price: Decimal = Field(default=0, ge=0, examples=[45000])

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên item không được để trống")
        return value


class ItemCreate(ItemBase):
    """Data accepted when creating an item."""


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Tên item không được để trống")
        return value

    @model_validator(mode="after")
    def require_update_fields(self) -> "ItemUpdate":
        if not self.model_fields_set:
            raise ValueError("Cần ít nhất một trường để cập nhật")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Tên item không được để trống")
        return self


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    price: float
    created_at: datetime
    updated_at: datetime
