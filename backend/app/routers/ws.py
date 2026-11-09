from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.core.security import decode_access_token
from app.core.ws_manager import ws_manager
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember

router = APIRouter(prefix="/ws", tags=["WebSocket Realtime"])


def _authenticate_ws_token(token: Optional[str]) -> Optional[int]:
    """Xác thực JWT access_token từ query param cho kết nối WebSocket."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        uid = payload.get("user_id") if payload.get("user_id") is not None else payload.get("sub")
        return int(uid) if uid is not None else None
    except (ValueError, TypeError):
        return None


@router.websocket("/projects/{project_id}")
async def websocket_project_board(
    websocket: WebSocket,
    project_id: int,
    token: Optional[str] = Query(None, description="JWT Access Token"),
):
    """
    WebSocket realtime cho bảng công việc của dự án.
    Nhận các sự kiện: list_created, list_updated, list_deleted, list_reordered,
    task_created, task_updated, task_moved, task_reordered, task_deleted, task_restored,
    comment_added, comment_updated, comment_deleted, checklist_updated.
    """
    user_id = _authenticate_ws_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token không hợp lệ hoặc thiếu")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            .first()
        )
        if not user or not project or not member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Không có quyền truy cập dự án")
            return
    finally:
        db.close()

    await ws_manager.connect_project(project_id, websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "project_id": project_id,
            "user_id": user_id,
            "message": "Đã kết nối realtime bảng dự án",
        })
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "project_id": project_id})
    except WebSocketDisconnect:
        ws_manager.disconnect_project(project_id, websocket)
    except Exception:
        ws_manager.disconnect_project(project_id, websocket)


@router.websocket("/notifications")
async def websocket_user_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT Access Token"),
):
    """
    WebSocket realtime cho chuông thông báo cá nhân của người dùng hiện tại.
    Nhận các sự kiện: notification_created, deadline_reminder.
    """
    user_id = _authenticate_ws_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token không hợp lệ hoặc thiếu")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Người dùng không hợp lệ")
            return
    finally:
        db.close()

    await ws_manager.connect_user(user_id, websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "user_id": user_id,
            "message": "Đã kết nối realtime chuông thông báo",
        })
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "user_id": user_id})
    except WebSocketDisconnect:
        ws_manager.disconnect_user(user_id, websocket)
    except Exception:
        ws_manager.disconnect_user(user_id, websocket)
