from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.project import router as project_router
from app.routers.project_members import router as project_members_router
from app.routers.invitations import router as invitations_router
from app.routers.invitations_public import router as invitations_public_router
from app.routers.label import router as label_router
from app.routers.task import router as task_router, my_tasks_router
from app.routers.checklist import router as checklist_router
from app.routers.comment import router as comment_router
from app.routers.attachment import router as attachment_router
from app.routers.notification import router as notification_router
from app.routers.activity_log import router as activity_log_router
from app.routers.ws import router as ws_router

__all__ = [
    "health_router",
    "auth_router",
    "project_router",
    "project_members_router",
    "invitations_router",
    "invitations_public_router",
    "label_router",
    "task_router",
    "my_tasks_router",
    "checklist_router",
    "comment_router",
    "attachment_router",
    "notification_router",
    "activity_log_router",
    "ws_router",
]
