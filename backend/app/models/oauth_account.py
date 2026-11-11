from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship
from app.db.session import Base


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    # users.id trong schema MySQL hiện có là BIGINT UNSIGNED, nên khóa ngoại
    # phải dùng đúng kiểu để MySQL chấp nhận khi tạo bảng OAuth.
    user_id = Column(BIGINT(unsigned=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # "google"
    provider_user_id = Column(String(255), nullable=False)

    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="oauth_accounts")

