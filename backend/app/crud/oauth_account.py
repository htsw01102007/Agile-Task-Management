"""Tìm hoặc tạo user từ hồ sơ OAuth đã được nhà cung cấp xác minh."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.email_policy import EmailRejectedError, normalize_real_email
from app.core.social import OAuthFlowError, SocialProfile
from app.crud import user as user_crud
from app.models.entities import User
from app.models.oauth_account import OAuthAccount


def _find_link(db: Session, provider: str, provider_user_id: str) -> OAuthAccount | None:
    return db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )


def _add_link(db: Session, user: User, profile: SocialProfile) -> None:
    db.add(
        OAuthAccount(
            user_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
        )
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise OAuthFlowError(409, "Tài khoản mạng xã hội này đã được liên kết") from error
    db.refresh(user)


def login_with_provider(db: Session, profile: SocialProfile) -> User:
    if not profile.provider_user_id:
        raise OAuthFlowError(401, "Nhà cung cấp không trả về mã người dùng")

    link = _find_link(db, profile.provider, profile.provider_user_id)
    if link is not None:
        user = db.get(User, link.user_id)
        if user is None or not user.is_active:
            raise OAuthFlowError(403, "Tài khoản đã bị vô hiệu hoá")
        return user

    if not profile.email or not profile.email_verified:
        raise OAuthFlowError(
            400,
            "Nhà cung cấp không cung cấp email đã xác minh. Hãy cấp quyền email hoặc dùng cách đăng nhập khác.",
        )

    try:
        email = normalize_real_email(profile.email)
    except EmailRejectedError as error:
        raise OAuthFlowError(400, str(error)) from error

    user = user_crud.get_user_by_email(db, email)
    if user is None:
        user = user_crud.create_social_user(
            db,
            email=email,
            full_name=profile.full_name,
            avatar_url=profile.avatar_url,
        )
    elif not user.is_active:
        raise OAuthFlowError(403, "Tài khoản đã bị vô hiệu hoá")

    _add_link(db, user, profile)
    return user
