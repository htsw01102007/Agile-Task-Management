from sqlalchemy import Column, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class TaskLabel(Base):
    __tablename__ = "task_labels"

    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    label_id = Column(BigInteger, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True, index=True)

    # Relationships
    task = relationship("Task", back_populates="labels")
    label = relationship("Label", back_populates="tasks")

