from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, false
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.common import ID, TimestampMixin


class ChecklistItem(TimestampMixin, Base):
    __tablename__ = "checklist_items"
    __table_args__ = (Index("ix_checklist_items_task_position", "task_id", "position"),)

    id = Column(ID, primary_key=True, autoincrement=True)
    task_id = Column(ID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(500), nullable=False)
    position = Column(Integer, nullable=False, default=0, server_default="0")
    is_done = Column(Boolean, nullable=False, default=False, server_default=false())
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task")

    def mark_done(self, done: bool) -> None:
        self.is_done = done
        self.completed_at = datetime.now() if done else None

    def __repr__(self) -> str:
        return f"<ChecklistItem id={self.id} task_id={self.task_id} done={self.is_done}>"
