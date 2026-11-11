from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, Enum, func, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(
        Enum(
            "task_created",
            "task_assigned",
            "task_updated",
            "task_moved",
            "task_completed",
            "task_deleted",
            "task_overdue",
            "task_due_soon",
            "comment_added",
            "comment_updated",
            "comment_deleted",
            "invitation_sent",
            "invitation_accepted",
            "invitation_declined",
            "member_added",
            "member_removed",
            "member_role_changed",
            "project_updated",
            "deadline_reminder",
            name="notification_type"
        ),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)  # "task", "comment", "project", etc.
    entity_id = Column(BigInteger, nullable=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    # Relationships
    user = relationship("User", back_populates="notifications")
    project = relationship("Project", back_populates="notifications")