import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import anyio
from fastapi import WebSocket, status


class ConnectionManager:
    """Quản lý kết nối WebSocket theo dự án (board realtime) và theo người dùng (chuông thông báo)."""

    def __init__(self) -> None:
        # project_id -> list[WebSocket]
        self.project_connections: Dict[int, List[WebSocket]] = {}
        # id(websocket) -> user_id
        self.ws_user_map: Dict[int, int] = {}
        # user_id -> list[WebSocket]
        self.user_connections: Dict[int, List[WebSocket]] = {}

    async def connect_project(self, project_id: int, websocket: WebSocket, user_id: Optional[int] = None) -> None:
        await websocket.accept()
        self.project_connections.setdefault(project_id, []).append(websocket)
        if user_id is not None:
            self.ws_user_map[id(websocket)] = user_id

    def disconnect_project(self, project_id: int, websocket: WebSocket) -> None:
        conns = self.project_connections.get(project_id, [])
        if websocket in conns:
            conns.remove(websocket)
        self.ws_user_map.pop(id(websocket), None)
        if not conns and project_id in self.project_connections:
            del self.project_connections[project_id]

    async def connect_user(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.user_connections.setdefault(user_id, []).append(websocket)

    def disconnect_user(self, user_id: int, websocket: WebSocket) -> None:
        conns = self.user_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns and user_id in self.user_connections:
            del self.user_connections[user_id]

    async def close_project_user(self, project_id: int, user_id: int, reason: str = "Quyền truy cập dự án đã thay đổi") -> None:
        conns = list(self.project_connections.get(project_id, []))
        for ws in conns:
            if self.ws_user_map.get(id(ws)) == user_id:
                self.disconnect_project(project_id, ws)
                try:
                    await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
                except Exception:
                    pass

    async def close_all_for_user(self, user_id: int, reason: str = "Phiên đăng nhập đã kết thúc") -> None:
        for pid in list(self.project_connections.keys()):
            await self.close_project_user(pid, user_id, reason=reason)
        u_conns = list(self.user_connections.get(user_id, []))
        for ws in u_conns:
            self.disconnect_user(user_id, ws)
            try:
                await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
            except Exception:
                pass

    async def broadcast_project(self, project_id: int, event_type: str, data: Any) -> None:
        conns = list(self.project_connections.get(project_id, []))
        if not conns:
            return
        message = {
            "event": event_type,
            "project_id": project_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        stale: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect_project(project_id, ws)

    async def broadcast_user(self, user_id: int, event_type: str, data: Any) -> None:
        conns = list(self.user_connections.get(user_id, []))
        if not conns:
            return
        message = {
            "event": event_type,
            "user_id": user_id,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        stale: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect_user(user_id, ws)


ws_manager = ConnectionManager()


def _run_async_from_sync(coro_func, *args) -> None:
    try:
        anyio.from_thread.run(coro_func, *args)
    except Exception:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(coro_func(*args))
        except Exception:
            pass


def notify_project_sync(project_id: int, event_type: str, data: Any) -> None:
    """Gửi sự kiện realtime tới tất cả client đang mở bảng của dự án (gọi từ hàm sync)."""
    if project_id not in ws_manager.project_connections:
        return
    _run_async_from_sync(ws_manager.broadcast_project, project_id, event_type, data)


def notify_user_sync(user_id: int, event_type: str, data: Any) -> None:
    """Gửi thông báo realtime tới chuông thông báo của người dùng (gọi từ hàm sync)."""
    if user_id not in ws_manager.user_connections:
        return
    _run_async_from_sync(ws_manager.broadcast_user, user_id, event_type, data)


def disconnect_project_user_sync(project_id: int, user_id: int, reason: str = "Quyền truy cập dự án đã thay đổi") -> None:
    """Đóng kết nối WebSocket bảng dự án của một user khi bị xoá hoặc rời dự án."""
    if project_id not in ws_manager.project_connections:
        return
    _run_async_from_sync(ws_manager.close_project_user, project_id, user_id, reason)


def disconnect_all_for_user_sync(user_id: int, reason: str = "Phiên đăng nhập đã kết thúc") -> None:
    """Đóng toàn bộ kết nối WebSocket của user khi đăng xuất hoặc đổi mật khẩu."""
    _run_async_from_sync(ws_manager.close_all_for_user, user_id, reason)
