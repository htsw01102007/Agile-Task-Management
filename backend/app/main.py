from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401
from app.core.config import settings
from app.db.session import Base, engine
from app.routers import (
    health_router, auth_router,
    project_router, project_members_router,
    invitations_router, invitations_public_router,
    label_router, task_router, my_tasks_router,
    checklist_router, comment_router, attachment_router,
    notification_router, activity_log_router, ws_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[DB] Đã kết nối MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except OperationalError as error:
        print("[DB] KHÔNG kết nối được MySQL! Kiểm tra MySQL đã bật chưa và file .env.")
        print(f"[DB] Chi tiết: {error.orig}")
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
    allow_credentials=True,
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

