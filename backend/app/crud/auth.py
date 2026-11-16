from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserOut,
    TokenResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_reset_token,
    hash_reset_token,
)
from app.core.config import settings


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        system_role=user.system_role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )


def ensure_active(user: User) -> None:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa"
        )


def issue_tokens(db: Session, user: User) -> TokenResponse:
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.system_role,
        "username": user.username,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=to_user_out(user),
    )


def register_user(db: Session, data: RegisterRequest) -> UserOut:
    email = data.email.lower()

    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng")

    if db.query(User).filter(func.lower(User.username) == data.username.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã được sử dụng")

    new_user = User(
        email=email,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        system_role="user",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return to_user_out(new_user)


def authenticate_user(db: Session, data: LoginRequest) -> TokenResponse:
    identifier = data.identifier.strip()
    identifier_lower = identifier.lower()

    user = (
        db.query(User)
        .filter(
            (func.lower(User.email) == identifier_lower) | 
            (func.lower(User.username) == identifier_lower)
        )
        .first()
    )

    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email/Tên đăng nhập hoặc mật khẩu không chính xác",
    )

    if user is None or user.password_hash is None:
        raise generic_error

    if not verify_password(data.password, user.password_hash):
        raise generic_error

    ensure_active(user)
    return issue_tokens(db, user)


def refresh_user_token(db: Session, refresh_token_str: str) -> TokenResponse:
    try:
        payload = decode_refresh_token(refresh_token_str)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")

    ensure_active(user)
    return issue_tokens(db, user)


def create_password_reset_token(db: Session, email: str) -> ForgotPasswordResponse:
    email_clean = email.lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()

    base_message = "Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được tạo."

    if not user or not user.is_active:
        return ForgotPasswordResponse(message=base_message)

    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)
    expires_at = datetime.now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({"used_at": datetime.now()})

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_record)
    db.commit()

    token_to_return = raw_token if settings.ENV == "development" else None
    return ForgotPasswordResponse(message=base_message, reset_token=token_to_return)


def reset_user_password(db: Session, token_str: str, new_password: str) -> MessageResponse:
    token_hash = hash_reset_token(token_str)
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    if not record or record.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã đặt lại mật khẩu không hợp lệ hoặc đã được sử dụng"
        )

    if record.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã đặt lại mật khẩu đã hết hạn"
        )

    user = record.user
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản không hợp lệ hoặc đã bị khóa")

    user.password_hash = hash_password(new_password)
    record.used_at = datetime.now()
    db.commit()

    return MessageResponse(message="Đặt lại mật khẩu thành công. Bạn có thể đăng nhập bằng mật khẩu mới.")


def update_user_profile(db: Session, current_user: User, data: UpdateProfileRequest) -> UserOut:
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url

    db.commit()
    db.refresh(current_user)
    return to_user_out(current_user)


def change_user_password(db: Session, current_user: User, data: ChangePasswordRequest) -> MessageResponse:
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đăng nhập qua Google chưa thiết lập mật khẩu cũ"
        )

    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác"
        )

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return MessageResponse(message="Đổi mật khẩu thành công")


def authenticate_google_user(
    db: Session,
    google_sub: str,
    email: str,
    full_name: str,
    avatar_url: str | None = None,
    google_token: dict | None = None
) -> TokenResponse:
    access_token = None
    refresh_token = None
    token_expires_at = None
    email_clean = email.lower()
    full_name_clean = (full_name or email_clean.split("@")[0])[:150]

    if google_token:
        access_token = google_token.get("access_token")
        refresh_token = google_token.get("refresh_token")
        expires_at_ts = google_token.get("expires_at")
        if expires_at_ts:
            token_expires_at = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc)

    oauth_account = (
        db.query(OAuthAccount)
        .filter(OAuthAccount.provider == "google", OAuthAccount.provider_user_id == google_sub)
        .first()
    )

    if oauth_account is not None:
        user = oauth_account.user
        ensure_active(user)
        if google_token:
            oauth_account.access_token = access_token
            if refresh_token:
                oauth_account.refresh_token = refresh_token
            oauth_account.token_expires_at = token_expires_at
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            db.commit()
    else:
        user = db.query(User).filter(func.lower(User.email) == email_clean).first()
        if user is None:
            base_username = email_clean.split("@")[0]
            base_username = "".join(c for c in base_username if c.isalnum() or c == "_")[:40] or "user"
            candidate_username = base_username
            counter = 1
            while db.query(User).filter(func.lower(User.username) == candidate_username.lower()).first():
                candidate_username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                email=email_clean,
                username=candidate_username,
                password_hash=None,
                full_name=full_name_clean,
                avatar_url=avatar_url,
                system_role="user",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        ensure_active(user)

        existing_link = (
            db.query(OAuthAccount)
            .filter(OAuthAccount.user_id == user.id, OAuthAccount.provider == "google")
            .first()
        )
        if existing_link is None:
            db.add(OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_sub,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at
            ))
            db.commit()
        else:
            existing_link.provider_user_id = google_sub
            if google_token:
                existing_link.access_token = access_token
                if refresh_token:
                    existing_link.refresh_token = refresh_token
                existing_link.token_expires_at = token_expires_at
            db.commit()

    return issue_tokens(db, user)
