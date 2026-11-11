from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Label(Base):
    __tablename__ = "labels"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # dạng hex: #22c55e
    created_by = Column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    tasks = relationship("TaskLabel", back_populates="label")
