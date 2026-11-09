"""
Đọc cấu hình từ file .env (không ghi bí mật vào source để commit).
Muốn thêm cấu hình mới: thêm 1 dòng vào class Settings
và khai báo biến tương ứng trong file .env / .env.example.
"""

from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/app/core/config.py -> thư mục gốc project (nơi đặt file .env duy nhất)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Task Project Management API"
    ENV: str = "development"

    # MySQL — bắt buộc khai báo trong .env, không có giá trị mặc định
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # JWT — bắt buộc trong .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Google OAuth2 — để trống nếu chưa dùng đăng nhập Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"

    @property
    def database_url(self) -> str:
        return (
            "mysql+pymysql://"
            f"{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()
