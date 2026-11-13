from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Null nếu chỉ dùng Google OAuth
    full_name = Column(String(150), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    system_role = Column(Enum("admin", "user"), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("ProjectInvitation", foreign_keys="ProjectInvitation.inviter_id", back_populates="inviter")
    received_invitations = relationship("ProjectInvitation", foreign_keys="ProjectInvitation.invitee_id", back_populates="invitee")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    # Task-related relationships
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    assigned_tasks = relationship("TaskAssignee", back_populates="user")
    task_comments = relationship("Comment", back_populates="user")
    uploaded_attachments = relationship("Attachment", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

