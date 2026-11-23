from sqlalchemy import Column, DateTime, ForeignKey, Index, func

from app.db.database import Base
from app.models.common import ID


class TaskAssignee(Base):
    __tablename__ = "task_assignees"
    __table_args__ = (Index("idx_ta_user", "user_id"),)

    task_id = Column(
        ID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    user_id = Column(
        ID,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    assigned_by = Column(ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<TaskAssignee task_id={self.task_id} user_id={self.user_id}>"
