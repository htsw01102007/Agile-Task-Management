from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False,
                        server_default=func.now(), onupdate=func.now())

    # Relationships
    owned_projects = relationship(
        "Project", back_populates="owner", foreign_keys="Project.owner_id")
    created_tasks = relationship(
        "Task", back_populates="creator", foreign_keys="Task.created_by")
    assigned_tasks = relationship("TaskAssignee", back_populates="user")
    project_memberships = relationship("ProjectMember", back_populates="user")
