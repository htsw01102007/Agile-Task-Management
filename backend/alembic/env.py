import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Đảm bảo import được package `app` dù chạy alembic từ đâu
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
# QUAN TRỌNG: các model trong app/models/* dùng Base của app.db.session
# (app.db.database có một Base khác, rỗng -> autogenerate sẽ đòi DROP toàn bộ bảng).
from app.db.session import Base
import app.models  # noqa: F401  - đăng ký tất cả model vào Base.metadata

config = context.config

# Lấy URL từ settings (đọc từ .env), không cần ghi vào alembic.ini.
# Phải đổi % thành %% vì configparser coi % là ký tự đặc biệt.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Không bao giờ để autogenerate DROP bảng có trong DB nhưng không có trong model
    (ví dụ bảng `items` cũ). Muốn xóa bảng thì tự viết tay trong migration."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()