from pathlib import Path
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


# Chỉ chứa placeholder chung chung, KHÔNG nhúng secret thật vào code
_INSECURE_DEFAULT_SECRETS = {
    "",
    "super-secret-key",
    "changeme",
}
_INSECURE_DEFAULT_DB_PASSWORDS = {
    "",
    "changeme",
}


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ROOT_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_DIR / ".env"), str(_BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Task Project Management API"
    ENV: str = "development"

    # MySQL Database credentials — mật khẩu thật đặt trong .env (gitignored)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "task_project_management"

    # JWT Security — SECRET_KEY thật đặt trong .env (gitignored)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True
    PASSWORD_RESET_URL: str = ""

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"
    UPLOAD_DIR: str = str(Path(__file__).resolve().parents[2] / "uploads")

    @property
    def database_url(self) -> str:
        # mysql+pymysql://user:password@host:port/database?charset=utf8mb4
        return (
            f"mysql+pymysql://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL not in origins and self.FRONTEND_URL:
            origins.append(self.FRONTEND_URL)
        return origins

    @property
    def cors_allow_credentials(self) -> bool:
        return self.cors_origin_list != ["*"]

    def validate_production_settings(self) -> None:
        """Chặn khởi động ở môi trường production nếu còn cấu hình mặc định không an toàn."""
        if self.ENV.strip().lower() != "production":
            return

        errors: list[str] = []
        if self.SECRET_KEY.strip() in _INSECURE_DEFAULT_SECRETS or len(self.SECRET_KEY.strip()) < 32:
            errors.append("SECRET_KEY phải được cấu hình riêng (>= 32 ký tự) ở môi trường production")
        if self.DB_PASSWORD in _INSECURE_DEFAULT_DB_PASSWORDS:
            errors.append("DB_PASSWORD không được để trống hoặc dùng mật khẩu mặc định ở môi trường production")
        if self.CORS_ORIGINS.strip() == "*" or "*" in self.cors_origin_list:
            errors.append("CORS_ORIGINS không được dùng '*' ở môi trường production")
        # Email configuration is validated when the password-reset delivery path is used.
        # Keep deployments that do not expose password reset backward compatible.

        if errors:
            raise RuntimeError("Cấu hình production không an toàn: " + "; ".join(errors))


settings = Settings()

