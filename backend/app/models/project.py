from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum("active", "completed", "archived"), nullable=False, default="active", index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    invitations = relationship("ProjectInvitation", back_populates="project", cascade="all, delete-orphan")
    lists = relationship("ListModel", back_populates="project", cascade="all, delete-orphan")
    labels = relationship("Label", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="project", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="project", cascade="all, delete-orphan")


