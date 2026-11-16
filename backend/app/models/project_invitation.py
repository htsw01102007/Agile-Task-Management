from sqlalchemy import Column, BigInteger, String, CHAR, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ProjectInvitation(Base):
    __tablename__ = "project_invitations"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    inviter_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    invitee_email = Column(String(255), nullable=False, index=True)
    invitee_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role = Column(Enum("manager", "member", "viewer"), nullable=False, default="member")
    # Lưu bản băm SHA-256 hex (64 ký tự) của token lời mời
    token = Column(CHAR(64), unique=True, nullable=False)
    status = Column(Enum("pending", "accepted", "declined", "expired", "cancelled"), nullable=False, default="pending", index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    responded_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="sent_invitations")
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="received_invitations")
