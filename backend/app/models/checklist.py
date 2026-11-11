from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(500), nullable=False)
    is_checked = Column(Boolean, nullable=False, default=False)
    position = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    task = relationship("Task", back_populates="checklist_items")
