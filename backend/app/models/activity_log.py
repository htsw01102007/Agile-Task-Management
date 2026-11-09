from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # "project", "task", "comment", "member", "invitation", "attachment"
    entity_id = Column(BigInteger, nullable=True)
    action = Column(String(50), nullable=False)  # "created", "updated", "deleted", "moved", "completed", "assigned", etc.
    old_value = Column(Text, nullable=True)  # JSON string
    new_value = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_activity_project_created", "project_id", "created_at"),
        Index("idx_activity_task_created", "task_id", "created_at"),
        Index("idx_activity_user_created", "user_id", "created_at"),
    )

    # Relationships
    project = relationship("Project", back_populates="activity_logs")
    task = relationship("Task", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")