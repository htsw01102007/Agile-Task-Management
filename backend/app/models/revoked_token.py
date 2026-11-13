from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base


class RevokedToken(Base):
    """Lưu định danh (jti) của các JWT đã bị thu hồi khi người dùng đăng xuất."""

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

