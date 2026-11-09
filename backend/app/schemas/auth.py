import re
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, AfterValidator


def check_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Mật khẩu phải có tối thiểu 8 ký tự")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ hoa")
    if not re.search(r"[a-z]", value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ thường")
    if not re.search(r"\d", value):
        raise ValueError("Mật khẩu phải có ít nhất một chữ số")
    return value


StrongPassword = Annotated[str, AfterValidator(check_password_strength)]


class RegisterRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: StrongPassword
    full_name: str = Field(min_length=1, max_length=150)


class LoginRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    identifier: str = Field(min_length=1, description="Email hoặc Username")
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    avatar_url: str | None = None
    system_role: str
    is_active: bool
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: StrongPassword


class MessageResponse(BaseModel):
    message: str


class UpdateProfileRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    avatar_url: str | None = Field(default=None, max_length=500)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: StrongPassword

