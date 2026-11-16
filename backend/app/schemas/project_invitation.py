from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class InvitationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    invitee_email: EmailStr
    role: str = Field("member", pattern="^(manager|member|viewer)$")


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    inviter_id: Optional[int] = None
    invitee_email: str
    invitee_id: Optional[int] = None
    role: str
    token: str = Field(..., description="Bản băm SHA-256 (64 ký tự hex) lưu trong CSDL")
    raw_token: Optional[str] = Field(
        None,
        description="Token gốc dùng để gửi qua email cho người nhận (chỉ trả về ngay lúc tạo lời mời)",
    )
    status: str
    expires_at: datetime
    created_at: datetime
    responded_at: Optional[datetime] = None
