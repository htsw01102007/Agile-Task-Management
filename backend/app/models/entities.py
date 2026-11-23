"""Core tables referenced by the task-management models."""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)

from app.db.database import Base
from app.models.common import ID


class User(Base):
    __tablename__ = "users"

    id = Column(ID, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    system_role = Column(
        Enum("admin", "user", name="user_system_role"),
        nullable=False,
        server_default="user",
    )
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(ID, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status = Column(
        Enum("active", "completed", "archived", name="project_status"),
        nullable=False,
        server_default="active",
    )
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)


class TaskList(Base):
    __tablename__ = "lists"
    __table_args__ = (
        UniqueConstraint("id", "project_id", name="uq_lists_id_project"),
    )

    id = Column(ID, primary_key=True, autoincrement=True)
    project_id = Column(
        ID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False, server_default="0")
    is_done_column = Column(Boolean, nullable=False, server_default=text("0"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["list_id", "project_id"],
            ["lists.id", "lists.project_id"],
            ondelete="CASCADE",
        ),
    )

    id = Column(ID, primary_key=True, autoincrement=True)
    project_id = Column(
        ID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    list_id = Column(ID, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, server_default="0")
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="task_priority"),
        nullable=False,
        server_default="medium",
    )
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)
