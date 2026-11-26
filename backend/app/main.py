import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.db.seed_demo import ensure_demo_seed_data
from app.routers import (
    health_router, auth_router,
    project_router, project_members_router,
    invitations_router, invitations_public_router,
    label_router, task_router, my_tasks_router,
    checklist_router, comment_router, attachment_router,
    notification_router, activity_log_router, ws_router,
    admin_router,
)


def _ensure_schema_migrations() -> None:
    """Bổ sung idempotent các cột mới nếu bảng đã tồn tại từ schema cũ."""
    inspector = inspect(engine)
    if inspector.has_table("users"):
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "token_version" not in user_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN token_version INT NOT NULL DEFAULT 0"))

    if inspector.has_table("tasks"):
        task_columns = {col["name"] for col in inspector.get_columns("tasks")}
        if "is_deleted" not in task_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE tasks ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE"))
                conn.execute(text("UPDATE tasks SET is_deleted = TRUE WHERE deleted_at IS NOT NULL"))

    if inspector.has_table("checklist_items"):
        ci_columns = {col["name"] for col in inspector.get_columns("checklist_items")}
        if "updated_at" not in ci_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE checklist_items ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    if inspector.has_table("comments"):
        cm_columns = {col["name"] for col in inspector.get_columns("comments")}
        if "updated_at" not in cm_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE comments ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    if inspector.has_table("attachments"):
        att_columns = {col["name"] for col in inspector.get_columns("attachments")}
        if "user_id" not in att_columns and "uploaded_by" in att_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE attachments ADD COLUMN user_id BIGINT NULL"))
                conn.execute(text("UPDATE attachments SET user_id = uploaded_by WHERE user_id IS NULL"))

    if inspector.has_table("notifications"):
        notif_columns = {col["name"] for col in inspector.get_columns("notifications")}
        with engine.begin() as conn:
            if "title" not in notif_columns:
                conn.execute(text("ALTER TABLE notifications ADD COLUMN title VARCHAR(255) NOT NULL DEFAULT 'Thông báo hệ thống'"))
            if "entity_type" not in notif_columns:
                conn.execute(text("ALTER TABLE notifications ADD COLUMN entity_type VARCHAR(50) NULL"))
            if "entity_id" not in notif_columns:
                conn.execute(text("ALTER TABLE notifications ADD COLUMN entity_id BIGINT NULL"))
            try:
                conn.execute(text("ALTER TABLE notifications MODIFY COLUMN type VARCHAR(50) NOT NULL"))
            except Exception:
                pass

    if inspector.has_table("project_invitations"):
        inv_columns = {col["name"] for col in inspector.get_columns("project_invitations")}
        if "pending_email" not in inv_columns:
            try:
                with engine.begin() as conn:
                    # Đóng các lời mời pending đã quá hạn trước khi thêm ràng buộc UNIQUE
                    conn.execute(text(
                        "UPDATE project_invitations SET status = 'expired' "
                        "WHERE status = 'pending' AND expires_at < UTC_TIMESTAMP()"
                    ))
                    conn.execute(text(
                        "ALTER TABLE project_invitations ADD COLUMN pending_email VARCHAR(255) "
                        "GENERATED ALWAYS AS (CASE WHEN status = 'pending' "
                        "THEN LOWER(invitee_email) ELSE NULL END) VIRTUAL"
                    ))
                    conn.execute(text(
                        "ALTER TABLE project_invitations ADD CONSTRAINT uq_invitations_pending "
                        "UNIQUE (project_id, pending_email)"
                    ))
            except Exception as error:  # dữ liệu cũ còn lời mời pending trùng
                print(f"[DB] Không thể thêm ràng buộc chống mời trùng pending: {error}")


settings.validate_production_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_production_settings()
    app.state.db_ready = False
    last_error: OperationalError | None = None
    max_attempts = 5

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            _ensure_schema_migrations()
            try:
                with SessionLocal() as seed_db:
                    if ensure_demo_seed_data(seed_db):
                        print("[DB] Đã tự động khởi tạo bộ dữ liệu mẫu nhóm Agile Workspace (Mật khẩu: Password@123)")
            except Exception as seed_err:
                print(f"[DB] Bỏ qua nạp dữ liệu mẫu tự động: {seed_err}")
            app.state.db_ready = True
            print(f"[DB] Đã kết nối MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
            break
        except OperationalError as error:
            last_error = error
            if attempt < max_attempts:
                await asyncio.sleep(1)

    if not app.state.db_ready and last_error is not None:
        print("[DB] KHÔNG kết nối được MySQL! Kiểm tra MySQL đã bật chưa và file .env.")
        print(f"[DB] Chi tiết: {last_error.orig}")
        if settings.ENV.strip().lower() == "production":
            raise RuntimeError("Không thể kết nối MySQL khi khởi động ở môi trường production") from last_error
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="API quản lý công việc và dự án - Agile Task Management",
    version="1.0.0",
    lifespan=lifespan
)

# SessionMiddleware cho Google OAuth CSRF state
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router với prefix /api
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

# Project Management routers
app.include_router(project_router, prefix="/api")
app.include_router(project_members_router, prefix="/api")
app.include_router(invitations_router, prefix="/api")
app.include_router(invitations_public_router, prefix="/api")
app.include_router(label_router, prefix="/api")

# Task & Sub-resource routers
app.include_router(my_tasks_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(checklist_router, prefix="/api")
app.include_router(comment_router, prefix="/api")
app.include_router(attachment_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(activity_log_router, prefix="/api")
app.include_router(ws_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} đang chạy.",
        "docs_url": "/docs",
        "api_prefix": "/api"
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
