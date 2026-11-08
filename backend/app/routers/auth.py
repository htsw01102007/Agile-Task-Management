from urllib.parse import quote_plus
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client.errors import OAuthError

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserOut,
    TokenResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    MessageResponse,
)
from app.models.user import User
from app.crud import auth as auth_crud

router = APIRouter(prefix="/auth", tags=["Auth & User"])

# ── 1. Đăng ký & Đăng nhập ────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=201, summary="Đăng ký tài khoản")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký tài khoản thông thường: Email, Username, Mật khẩu mạnh, Họ tên."""
    return auth_crud.register_user(db, body)


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập tài khoản")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập bằng Email hoặc Username + Mật khẩu. Trả về access_token + refresh_token."""
    return auth_crud.authenticate_user(db, body)


# ── 2. Làm mới Token ──────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse, summary="Làm mới access token bằng refresh token")
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """Sử dụng refresh_token để lấy cặp access_token và refresh_token mới."""
    return auth_crud.refresh_user_token(db, body.refresh_token)


# ── 3. Quên mật khẩu & Đặt lại mật khẩu ───────────────────
@router.post("/forgot-password", response_model=ForgotPasswordResponse, summary="Yêu cầu đặt lại mật khẩu")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Tạo token đặt lại mật khẩu có thời hạn 30 phút lưu vào DB."""
    return auth_crud.create_password_reset_token(db, body.email)


@router.post("/reset-password", response_model=MessageResponse, summary="Đặt lại mật khẩu bằng token")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Xác thực token và cập nhật mật khẩu mới."""
    return auth_crud.reset_user_password(db, body.token, body.new_password)


# ── 4. Quản lý Người dùng Hiện tại (Me) ───────────────────
@router.get("/me", response_model=UserOut, summary="Lấy thông tin người dùng hiện tại")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Xem thông tin chi tiết tài khoản hiện tại."""
    return auth_crud.to_user_out(current_user)


@router.put("/me", response_model=UserOut, summary="Cập nhật hồ sơ cá nhân")
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật họ tên hoặc ảnh đại diện (avatar_url)."""
    return auth_crud.update_user_profile(db, current_user, body)


@router.post("/me/change-password", response_model=MessageResponse, summary="Đổi mật khẩu người dùng hiện tại")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Đổi mật khẩu với mật khẩu cũ và mật khẩu mới."""
    return auth_crud.change_user_password(db, current_user, body)


# ── 5. Google OAuth2 Authentication ───────────────────────
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def _is_invalid_client_config(client_id: str, client_secret: str) -> bool:
    if not client_id or not client_secret:
        return True
    if "your-google-client-id" in client_id or "your-google-client-secret" in client_secret:
        return True
    return False


@router.get("/google/login", summary="Bắt đầu đăng nhập bằng Google OAuth2")
async def google_login(request: Request):
    if _is_invalid_client_config(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET):
        error_msg = "Google OAuth2 chưa được cấu hình Client ID và Secret hợp lệ trong file .env."
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error={quote_plus(error_msg)}")

    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )


@router.get("/google/callback", summary="Callback xử lý phản hồi từ Google OAuth2")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        if not token:
            raise ValueError("Không nhận được token từ Google")

        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await oauth.google.userinfo(token=token)

        if not userinfo or not userinfo.get("email"):
            raise ValueError("Không thể trích xuất email từ tài khoản Google")

        if userinfo.get("email_verified") is not True:
            raise ValueError("Email Google của bạn chưa được xác minh")

        google_sub = userinfo.get("sub") or userinfo.get("id")
        if not google_sub:
            raise ValueError("Không tìm thấy ID định danh từ tài khoản Google")

        email = userinfo["email"]
        full_name = userinfo.get("name") or userinfo.get("given_name") or email.split("@")[0]
        avatar_url = userinfo.get("picture")

        token_response = auth_crud.authenticate_google_user(
            db,
            google_sub=str(google_sub),
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
            google_token=token,
        )

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/callback#access_token={token_response.access_token}&refresh_token={token_response.refresh_token}"
        )

    except HTTPException as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback?error={quote_plus(str(e.detail))}")
    except OAuthError as e:
        error_msg = f"Lỗi xác thực Google: {e.description if hasattr(e, 'description') and e.description else str(e)}"
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback?error={quote_plus(error_msg)}")
    except Exception as e:
        error_msg = f"Đăng nhập Google thất bại: {str(e)}"
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/callback?error={quote_plus(error_msg)}")

