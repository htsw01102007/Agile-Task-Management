from urllib.parse import quote_plus
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Task Project Management API"
    ENV: str = "development"

    # MySQL Database credentials
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "task_project_management"

    # JWT Security
    SECRET_KEY: str = "37da485fb46bad455e73ea0f2e2594ceedb41fb57dc221bfc4314288de3a22e4"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"

    # First system administrator; set these values in the repository-root .env.
    ADMIN_EMAIL: str = ""
    ADMIN_USERNAME: str = ""
    ADMIN_FULL_NAME: str = "Quản trị hệ thống"
    ADMIN_PASSWORD: str = ""

    @property
    def database_url(self) -> str:
        # mysql+pymysql://user:password@host:port/database?charset=utf8mb4
        return (
            f"mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
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


settings = Settings()
