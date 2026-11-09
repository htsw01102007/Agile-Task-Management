"""Đọc / ghi bảng users cho đăng ký và đăng nhập."""
import re
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.lower()))


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    full_name: str,
    password: str,
    avatar_url: str | None = None,
) -> User:
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_social_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    avatar_url: str | None,
) -> User:
    username = _unique_username(db, email)
    return create_user(
        db,
        email=email,
        username=username,
        full_name=full_name,
        password=secrets.token_urlsafe(32),
        avatar_url=avatar_url,
    )


def _unique_username(db: Session, email: str) -> str:
    local = email.split("@", 1)[0]
    base = re.sub(r"[^A-Za-z0-9_]", "", local)[:40] or "user"
    if len(base) < 3:
        base = f"user_{base}"[:40]
    candidate = base
    suffix = 1
    while get_user_by_username(db, candidate) is not None:
        candidate = f"{base[:40]}_{suffix}"
        suffix += 1
    return candidate[:50]
