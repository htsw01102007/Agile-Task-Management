import re

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


def provision_initial_admin(db: Session) -> bool:
    """Create the configured first administrator once; never reset an existing password."""
    email = settings.ADMIN_EMAIL.strip().lower()
    username = settings.ADMIN_USERNAME.strip()
    password = settings.ADMIN_PASSWORD
    configured = (email, username, password)

    if not any(configured):
        return False
    if not all(configured):
        raise RuntimeError("Set ADMIN_EMAIL, ADMIN_USERNAME, and ADMIN_PASSWORD together in the root .env.")
    if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password):
        raise RuntimeError("ADMIN_PASSWORD must be at least 8 characters and contain uppercase, lowercase, and a digit.")

    existing = db.query(User).filter(
        or_(func.lower(User.email) == email, func.lower(User.username) == username.lower())
    ).first()
    if existing:
        if existing.email.lower() != email or existing.username.lower() != username.lower():
            raise RuntimeError("ADMIN_EMAIL or ADMIN_USERNAME already belongs to a different account.")
        if existing.system_role != "admin":
            existing.system_role = "admin"
            db.commit()
            return True
        return False

    db.add(User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        full_name=settings.ADMIN_FULL_NAME.strip() or "Quản trị hệ thống",
        system_role="admin",
        is_active=True,
    ))
    db.commit()
    return True
