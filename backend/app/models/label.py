from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.common import ID, TimestampMixin


class Label(TimestampMixin, Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
    )

    id = Column(ID, primary_key=True, autoincrement=True)
    project_id = Column(ID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(CHAR(7), nullable=False, server_default="#808080")

    project = relationship("Project")
    task_links = relationship(
        "TaskLabel",
        back_populates="label",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tasks = relationship("Task", secondary="task_labels", viewonly=True)

    def __repr__(self) -> str:
        return f"<Label id={self.id} project_id={self.project_id} name={self.name!r}>"


class TaskLabel(Base):
    __tablename__ = "task_labels"
    __table_args__ = (Index("ix_task_labels_label_id", "label_id"),)

    task_id = Column(
        ID,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    label_id = Column(
        ID,
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    task = relationship("Task")
    label = relationship("Label", back_populates="task_links")

    def __repr__(self) -> str:
        return f"<TaskLabel task_id={self.task_id} label_id={self.label_id}>"
