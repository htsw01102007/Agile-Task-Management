from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(BigInteger, ForeignKey(
        "users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False,
                        server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[
                         owner_id], back_populates="owned_projects")
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan")
    lists = relationship("ListModel", back_populates="project",
                         cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project",
                         cascade="all, delete-orphan")
