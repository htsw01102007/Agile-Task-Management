from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.routers import (
    health_router, auth_router,
    project_router, project_members_router,
    invitations_router, invitations_public_router,
    label_router, task_router, my_tasks_router,
    checklist_router, comment_router, attachment_router,
    notification_router, activity_log_router, ws_router,
    admin_users_router,
)
from app.core.bootstrap import provision_initial_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[DB] Connected to MySQL {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        with SessionLocal() as db:
            if provision_initial_admin(db):
                print("[ADMIN] Administrator account provisioned from .env.")
            elif settings.ADMIN_EMAIL and settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD:
                print("[ADMIN] Configured administrator already exists.")
            else:
                print("[ADMIN] Initial administrator is not configured; set ADMIN_* values in .env.")
    except OperationalError as error:
        # Keep the API alive so /api/health can return a useful 503 response.
        # ASCII output avoids crashing under a Windows cp1252 console.
        print("[DB] Cannot initialize MySQL. Check the service and .env.")
        print(f"[DB] Detail: {error.orig}")
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
app.include_router(admin_users_router, prefix="/api")

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


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} đang chạy.",
        "docs_url": "/docs",
        "api_prefix": "/api"
    }
