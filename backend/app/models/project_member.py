from sqlalchemy import Column, BigInteger, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    role = Column(Enum("owner", "manager", "member", "viewer"), nullable=False, default="member")
    joined_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

