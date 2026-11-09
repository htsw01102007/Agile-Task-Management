from sqlalchemy import Column, BigInteger, String, CHAR, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class Label(Base):
    __tablename__ = "labels"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(CHAR(7), nullable=False, default="#808080")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
    )

    # Relationships
    project = relationship("Project", back_populates="labels")
    tasks = relationship("TaskLabel", back_populates="label")
