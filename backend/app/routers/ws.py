import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.core.security import decode_access_token, get_token_identifier
from app.core.ws_manager import ws_manager
from app.db.session import SessionLocal
from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.models.project import Project
from app.models.project_member import ProjectMember

router = APIRouter(prefix="/ws", tags=["WebSocket Realtime"])
WS_REVALIDATE_INTERVAL_SECONDS = 30.0


def _extract_ws_claims(token: Optional[str]) -> Optional[dict]:
    """Giải mã JWT access_token từ query param cho WebSocket."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        uid = payload.get("user_id")
        if uid is None:
            return None
        token_id = get_token_identifier(token, payload)
        check_ids = [token_id]
        if payload.get("sid"):
            check_ids.append(str(payload["sid"]))
        return {
            "user_id": int(uid),
            "check_ids": check_ids,
            "token_version": payload.get("token_version", 0),
        }
    except (ValueError, TypeError):
        return None


def _is_ws_access_valid(claims: dict, project_id: Optional[int] = None) -> bool:
    """Kiểm tra lại DB xem token chưa bị thu hồi, user còn active và còn quyền dự án."""
    db = SessionLocal()
    try:
        if db.query(RevokedToken.id).filter(RevokedToken.jti.in_(claims["check_ids"])).first() is not None:
            return False
        user = db.query(User).filter(User.id == claims["user_id"], User.is_active.is_(True)).first()
        if not user or claims["token_version"] != (user.token_version or 0):
            return False
        if project_id is not None:
            project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
            member = (
                db.query(ProjectMember)
                .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == claims["user_id"])
                .first()
            )
            if not project or not member:
                return False
        return True
    finally:
        db.close()


def _authenticate_ws_token(token: Optional[str]) -> Optional[int]:
    """Xác thực JWT access_token từ query param cho kết nối WebSocket (kiểm tra cả thu hồi token)."""
    claims = _extract_ws_claims(token)
    if not claims or not _is_ws_access_valid(claims):
        return None
    return claims["user_id"]


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
    claims = _extract_ws_claims(token)
    if not claims or not _is_ws_access_valid(claims):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token không hợp lệ hoặc thiếu")
        return

    user_id = claims["user_id"]
    if not _is_ws_access_valid(claims, project_id=project_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Không có quyền truy cập dự án")
        return

    await ws_manager.connect_project(project_id, websocket, user_id=user_id)
    try:
        await websocket.send_json({
            "event": "connected",
            "project_id": project_id,
            "user_id": user_id,
            "message": "Đã kết nối realtime bảng dự án",
        })
        while True:
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=WS_REVALIDATE_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                if not _is_ws_access_valid(claims, project_id=project_id):
                    await websocket.close(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Phiên hoặc quyền truy cập dự án không còn hợp lệ",
                    )
                    break
                continue

            if not _is_ws_access_valid(claims, project_id=project_id):
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Phiên hoặc quyền truy cập dự án không còn hợp lệ",
                )
                break

            if msg.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "project_id": project_id})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
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
    claims = _extract_ws_claims(token)
    if not claims or not _is_ws_access_valid(claims):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token không hợp lệ hoặc thiếu")
        return

    user_id = claims["user_id"]
    await ws_manager.connect_user(user_id, websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "user_id": user_id,
            "message": "Đã kết nối realtime chuông thông báo",
        })
        while True:
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=WS_REVALIDATE_INTERVAL_SECONDS,
                )
            except asyncio.TimeoutError:
                if not _is_ws_access_valid(claims):
                    await websocket.close(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Phiên đăng nhập không còn hợp lệ",
                    )
                    break
                continue

            if not _is_ws_access_valid(claims):
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Phiên đăng nhập không còn hợp lệ",
                )
                break

            if msg.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "user_id": user_id})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        ws_manager.disconnect_user(user_id, websocket)
