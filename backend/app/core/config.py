"""
Đọc cấu hình từ file .env (không đẩy môi trường thật lên Git).
Muốn thêm cấu hình mới: thêm 1 dòng vào class Settings
và khai báo biến tương ứng trong file .env.
"""

from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


# Xác định thư mục gốc của project Agile-Task-Management
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Đọc cấu hình từ file .env ở thư mục gốc project
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "KS25 Base API"

    # Database configuration
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # CORS
    CORS_ORIGINS: str = "*"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://"
            f"{quote_plus(self.DB_USER)}:"
            f"{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()