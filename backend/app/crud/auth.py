from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.models.password_reset_token import PasswordResetToken
from app.models.revoked_token import RevokedToken
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
    decode_access_token,
    decode_refresh_token,
    get_token_identifier,
    generate_reset_token,
    hash_reset_token,
)
from app.core.config import settings
from app.core.ws_manager import disconnect_all_for_user_sync


def _utc_now_naive() -> datetime:
    """Trả về thời gian UTC hiện tại dạng naive để lưu đồng nhất vào cột DATETIME của MySQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    user.last_login_at = _utc_now_naive()
    db.commit()
    db.refresh(user)

    session_id = str(uuid.uuid4())
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.system_role,
        "username": user.username,
        "sid": session_id,
        "token_version": user.token_version or 0,
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
        token_version=0,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return to_user_out(new_user)


def authenticate_user(db: Session, data: LoginRequest) -> TokenResponse:
    identifier = data.identifier.strip()
    identifier_lower = identifier.lower()

    if identifier_lower.endswith("@agileworkspace.vn") or identifier_lower in {
        "admin", "nghiemdinhbinh", "nguyenquydung", "leminhson", "haducminh", "nguyentandung", "minhduong"
    }:
        from app.db.seed_demo import ensure_demo_seed_data
        try:
            ensure_demo_seed_data(db)
        except Exception as seed_exc:
            db.rollback()
            print(f"[Auth Seed Warning] {seed_exc}")

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

    token_id = get_token_identifier(refresh_token_str, payload)
    check_ids = [token_id]
    if payload.get("sid"):
        check_ids.append(str(payload["sid"]))
    if db.query(RevokedToken.id).filter(RevokedToken.jti.in_(check_ids)).first() is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token đã bị thu hồi")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")

    if payload.get("token_version", 0) != (user.token_version or 0):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập đã hết hiệu lực")

    ensure_active(user)

    # Thu hồi refresh token cũ (rotation) trước khi cấp cặp mới
    now = datetime.now(timezone.utc)
    exp_ts = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else now
    if db.query(RevokedToken.id).filter(RevokedToken.jti == token_id).first() is None:
        db.add(RevokedToken(jti=token_id, expires_at=expires_at))
        db.flush()

    return issue_tokens(db, user)


def create_password_reset_token(db: Session, email: str) -> ForgotPasswordResponse:
    email_clean = email.lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()

    base_message = "Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được tạo."

    if not user or not user.is_active:
        return ForgotPasswordResponse(message=base_message)

    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)
    now_naive = _utc_now_naive()
    expires_at = now_naive + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update({"used_at": now_naive})

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

    now_naive = _utc_now_naive()
    exp_dt = record.expires_at
    if exp_dt.tzinfo is not None:
        exp_dt = exp_dt.astimezone(timezone.utc).replace(tzinfo=None)
    if exp_dt < now_naive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã đặt lại mật khẩu đã hết hạn"
        )

    user = record.user
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản không hợp lệ hoặc đã bị khóa")

    user.password_hash = hash_password(new_password)
    user.token_version = (user.token_version or 0) + 1
    record.used_at = now_naive
    db.commit()

    disconnect_all_for_user_sync(user.id, reason="Mật khẩu đã được đặt lại")
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
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()

    disconnect_all_for_user_sync(current_user.id, reason="Mật khẩu đã thay đổi")
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
                token_version=0,
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


def logout_user(
    db: Session,
    token: str,
    refresh_token_str: str | None = None,
    user_id: int | None = None,
) -> MessageResponse:
    payload = decode_access_token(token)
    token_id = get_token_identifier(token, payload)
    now = datetime.now(timezone.utc)
    exp_ts = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else now
    refresh_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete(synchronize_session=False)

    uid = user_id or payload.get("user_id")
    ids_to_revoke = [(token_id, expires_at)]
    if payload.get("sid"):
        ids_to_revoke.append((str(payload["sid"]), refresh_exp))

    if refresh_token_str:
        try:
            ref_payload = decode_refresh_token(refresh_token_str)
            ref_uid = ref_payload.get("user_id")
            if uid is not None and ref_uid != int(uid):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Refresh token không thuộc về người dùng hiện tại",
                )
            if not (payload.get("sid") and ref_payload.get("sid") and ref_payload.get("sid") != payload.get("sid")):
                ref_id = get_token_identifier(refresh_token_str, ref_payload)
                ref_exp_ts = ref_payload.get("exp")
                ref_exp = datetime.fromtimestamp(ref_exp_ts, tz=timezone.utc) if ref_exp_ts else refresh_exp
                ids_to_revoke.append((ref_id, ref_exp))
        except ValueError:
            pass

    seen = set()
    for jti_val, exp_val in ids_to_revoke:
        if jti_val in seen:
            continue
        seen.add(jti_val)
        if db.query(RevokedToken.id).filter(RevokedToken.jti == jti_val).first() is None:
            db.add(RevokedToken(jti=jti_val, expires_at=exp_val))

    db.commit()
    if uid is not None:
        disconnect_all_for_user_sync(int(uid), reason="Đã đăng xuất")
    return MessageResponse(message="Đăng xuất thành công")
