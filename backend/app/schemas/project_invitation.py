from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class InvitationCreate(BaseModel):
    invitee_email: EmailStr
    role: str = Field("member", pattern="^(manager|member|viewer)$")


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    inviter_id: int
    invitee_email: str
    invitee_id: Optional[int] = None
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime
    responded_at: Optional[datetime] = None
