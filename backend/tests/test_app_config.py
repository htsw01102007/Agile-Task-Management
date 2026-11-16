import re
import asyncio
from pathlib import Path
from urllib.parse import urlparse

from starlette.requests import Request

from app.core.config import Settings, settings
from app.routers import auth


ROOT = Path(__file__).resolve().parents[2]


def test_database_name_matches_example_compose_and_schema() -> None:
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    compose = (ROOT / "backend" / "docker-compose.yml").read_text(encoding="utf-8")
    schema = (ROOT / "backend" / "sql" / "init.sql").read_text(encoding="utf-8")

    env_name = re.search(r"^DB_NAME=(\w+)$", env_example, re.MULTILINE)
    compose_name = re.search(r"^\s+MYSQL_DATABASE:\s*(\w+)$", compose, re.MULTILINE)
    schema_name = re.search(r"^CREATE DATABASE IF NOT EXISTS\s+(\w+)", schema, re.MULTILINE)

    assert env_name is not None
    assert compose_name is not None
    assert schema_name is not None
    assert env_name.group(1) == compose_name.group(1) == schema_name.group(1)
    assert Settings(_env_file=None).DB_NAME == schema_name.group(1)
    assert "./sql/init.sql:/docker-entrypoint-initdb.d/" in compose
    assert "./sql:/docker-entrypoint-initdb.d" not in compose


def test_database_url_quotes_credentials() -> None:
    configured = Settings(
        _env_file=None,
        DB_USER="user@host",
        DB_PASSWORD="p@ss/word#",
        DB_NAME="agile_task_management",
    )

    assert configured.database_url == (
        "mysql+pymysql://user%40host:p%40ss%2Fword%23"
        "@127.0.0.1:3306/agile_task_management?charset=utf8mb4"
    )


def test_unconfigured_google_login_redirects_to_login(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/auth/google/login",
            "raw_path": b"/api/auth/google/login",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 1),
            "server": ("127.0.0.1", 8000),
        }
    )

    response = asyncio.run(auth.google_login(request))

    assert response.status_code == 307
    assert urlparse(response.headers["location"]).path.endswith("/pages/login.html")
