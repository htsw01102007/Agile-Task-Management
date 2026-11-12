"""Các bảng phụ thuộc task: bình luận, đính kèm, nhật ký hoạt động.

Ba model này được khai báo tối thiểu để relationship("Comment"/"Attachment"/
"ActivityLog") trong Task resolve được khi SQLAlchemy cấu hình mapper.
"""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    task = relationship("Task", back_populates="comments")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    task = relationship("Task", back_populates="attachments")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    task = relationship("Task", back_populates="activity_logs")
