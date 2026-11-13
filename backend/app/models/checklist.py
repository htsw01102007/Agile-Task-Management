from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(500), nullable=False)
    is_done = Column(Boolean, nullable=False, default=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    task = relationship("Task", back_populates="checklist_items")