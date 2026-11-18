from sqlalchemy import BigInteger, Column, DateTime, Integer, func
from sqlalchemy.dialects.mysql import BIGINT

ID = (
    BigInteger()
    .with_variant(BIGINT(unsigned=True), "mysql")
    .with_variant(Integer, "sqlite")
)


class TimestampMixin:
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
