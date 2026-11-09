from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None


class AttachmentUploadResponse(BaseModel):
    """Response sau khi upload file"""
    id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    download_url: str