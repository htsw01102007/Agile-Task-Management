import hashlib
import secrets
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


# ── Password Hashing ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# ── JWT Handling ──────────────────────────────────────────────────
def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    payload = data.copy()
    minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload["type"] = ACCESS_TOKEN_TYPE
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_days: int | None = None) -> str:
    payload = data.copy()
    days = expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
    payload["type"] = REFRESH_TOKEN_TYPE
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=days)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token đã hết hạn")
    except jwt.InvalidTokenError:
        raise ValueError("Token không hợp lệ")

    if payload.get("type") != expected_type:
        raise ValueError("Loại token không hợp lệ")
    return payload


def decode_access_token(token: str) -> dict:
    return _decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> dict:
    return _decode_token(token, REFRESH_TOKEN_TYPE)


# ── Token đặt lại mật khẩu ────────────────────────────────────────
def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

