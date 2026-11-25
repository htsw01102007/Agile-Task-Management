"""OAuth 2.0 / OpenID Connect cho Google.

Backend đổi authorization code lấy token, rồi kiểm tra chữ ký id_token
bằng khóa công khai của Google. Client secret không rời khỏi server.
"""
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt
from jwt import PyJWKClient

from app.core.config import settings

_TIMEOUT_SECONDS = 10
_google_jwks: PyJWKClient | None = None


class OAuthFlowError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass
class SocialProfile:
    provider: str
    provider_user_id: str
    email: str | None
    email_verified: bool
    full_name: str
    avatar_url: str | None


def _read_json(url: str, *, data: bytes | None = None) -> dict:
    request = Request(url, data=data, method="POST" if data is not None else "GET")
    if data is not None:
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error.read()
        raise OAuthFlowError(401, "Nhà cung cấp từ chối mã đăng nhập") from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise OAuthFlowError(503, "Không kết nối được nhà cung cấp đăng nhập") from error


def _verified(value) -> bool:
    return value is True or str(value).lower() == "true"


def _avatar(value) -> str | None:
    if isinstance(value, str) and len(value) <= 500:
        return value
    return None


def _decode_id_token(id_token: str, jwks: PyJWKClient, *, audience: str, issuers: set[str]) -> dict:
    try:
        key = jwks.get_signing_key_from_jwt(id_token).key
        payload = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=audience,
            issuer=list(issuers),
        )
    except (jwt.PyJWTError, TimeoutError, OSError) as error:
        raise OAuthFlowError(401, "Token đăng nhập không hợp lệ hoặc đã hết hạn") from error
    if not isinstance(payload, dict):
        raise OAuthFlowError(401, "Token đăng nhập không hợp lệ")
    return payload


def _google_jwks_client() -> PyJWKClient:
    global _google_jwks
    if _google_jwks is None:
        _google_jwks = PyJWKClient("https://www.googleapis.com/oauth2/v3/certs", timeout=_TIMEOUT_SECONDS)
    return _google_jwks


def _profile_from_google(payload: dict) -> SocialProfile:
    subject = str(payload.get("sub") or "")
    email = payload.get("email")
    if not subject:
        raise OAuthFlowError(401, "Google không trả về mã người dùng")
    name = payload.get("name") or (str(email).split("@", 1)[0] if email else "Google user")
    return SocialProfile(
        provider="google",
        provider_user_id=subject,
        email=str(email) if email else None,
        email_verified=_verified(payload.get("email_verified")),
        full_name=str(name)[:150],
        avatar_url=_avatar(payload.get("picture")),
    )


def exchange_google_code(code: str) -> SocialProfile:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise OAuthFlowError(503, "Chưa cấu hình Google OAuth")
    payload = _read_json(
        "https://oauth2.googleapis.com/token",
        data=urlencode(
            {
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        ).encode(),
    )
    id_token = payload.get("id_token")
    if not id_token:
        raise OAuthFlowError(401, "Google không trả về id_token")
    claims = _decode_id_token(
        id_token,
        _google_jwks_client(),
        audience=settings.GOOGLE_CLIENT_ID,
        issuers={"https://accounts.google.com", "accounts.google.com"},
    )
    return _profile_from_google(claims)


def verify_google_id_token(id_token: str) -> SocialProfile:
    if not settings.GOOGLE_CLIENT_ID:
        raise OAuthFlowError(503, "Chưa cấu hình GOOGLE_CLIENT_ID")
    claims = _decode_id_token(
        id_token,
        _google_jwks_client(),
        audience=settings.GOOGLE_CLIENT_ID,
        issuers={"https://accounts.google.com", "accounts.google.com"},
    )
    return _profile_from_google(claims)
