from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Index, String, event, func
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.activity_enums import EntityType
from app.models.common import ID


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_project_created", "project_id", "created_at"),
        Index("ix_activity_logs_task_created", "task_id", "created_at"),
    )

    id = Column(ID, primary_key=True, autoincrement=True)
    project_id = Column(ID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(ID, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(
        Enum(
            EntityType,
            name="activity_entity_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    entity_id = Column(ID, nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    project = relationship("Project")
    task = relationship("Task")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ActivityLog id={self.id} action={self.action} entity={self.entity_type}:{self.entity_id}>"


@event.listens_for(ActivityLog, "before_update")
def _block_update(mapper, connection, target):
    raise RuntimeError("activity_logs is append-only and cannot be updated")


@event.listens_for(ActivityLog, "before_delete")
def _block_delete(mapper, connection, target):
    raise RuntimeError("activity_logs is append-only and cannot be deleted")
