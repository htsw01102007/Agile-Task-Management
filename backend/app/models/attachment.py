from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # relative path under /uploads
    file_size = Column(BigInteger, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    task = relationship("Task", back_populates="attachments")
    user = relationship("User", back_populates="uploaded_attachments")
