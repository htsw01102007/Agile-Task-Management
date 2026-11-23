from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, ForeignKey, Index, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class ListModel(Base):
    __tablename__ = "lists"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    is_done_column = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_lists_id_project"),
        Index("idx_lists_project_position", "project_id", "position"),
    )

    # Relationships
    project = relationship("Project", back_populates="lists")
    tasks = relationship("Task", back_populates="list", cascade="all, delete-orphan")
