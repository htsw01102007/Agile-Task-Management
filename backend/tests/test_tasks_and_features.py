import io
import os
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import app


def _setup_project_with_list(client, test_user_factory):
    owner = test_user_factory("towner")
    member = test_user_factory("tmember")
    outsider = test_user_factory("toutside")

    proj = client.post(
        "/api/projects",
        headers=owner["headers"],
        json={"name": "Task Feature Project"},
    ).json()
    project_id = proj["id"]
    test_user_factory.track_project(project_id)

    test_user_factory.invite_member(owner["headers"], project_id, member, role="member")

    lst = client.post(
        f"/api/projects/{project_id}/lists",
        headers=owner["headers"],
        json={"name": "To Do"},
    )
    assert lst.status_code == 201, lst.text
    list_id = lst.json()["id"]
    return owner, member, outsider, project_id, list_id


def test_health_endpoint_checks_database(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_task_creation_ordering_and_priority_sort(client, test_user_factory):
    owner, member, _, project_id, list_id = _setup_project_with_list(client, test_user_factory)

    t1 = client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={"list_id": list_id, "title": "Low Task", "priority": "low"},
    )
    t2 = client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={"list_id": list_id, "title": "Urgent Task", "priority": "urgent"},
    )
    assert t1.status_code == 201 and t2.status_code == 201
    t1_id, t2_id = t1.json()["id"], t2.json()["id"]
    assert t1.json()["position"] == 0
    assert t2.json()["position"] == 1

    # Reorder tasks
    reorder = client.patch(
        f"/api/projects/{project_id}/tasks/reorder",
        headers=member["headers"],
        json={"task_ids": [t2_id, t1_id]},
    )
    assert reorder.status_code == 200

    by_pos = client.get(
        f"/api/projects/{project_id}/tasks",
        headers=member["headers"],
        params={"list_id": list_id, "sort_by": "position"},
    ).json()
    assert [t["id"] for t in by_pos] == [t2_id, t1_id]

    by_prio = client.get(
        f"/api/projects/{project_id}/tasks",
        headers=member["headers"],
        params={"list_id": list_id, "sort_by": "priority", "order": "desc"},
    ).json()
    assert by_prio[0]["priority"] == "urgent"
    assert by_prio[-1]["priority"] == "low"


def test_notification_creation_requires_owner_or_manager(client, test_user_factory):
    owner, member, outsider, project_id, _ = _setup_project_with_list(client, test_user_factory)

    # Member cannot broadcast/create notifications for others
    forbidden = client.post(
        "/api/notifications",
        headers=member["headers"],
        json={
            "user_id": owner["id"],
            "project_id": project_id,
            "type": "invitation_sent",
            "title": "Thông báo",
            "message": "Unauthorized notif",
        },
    )
    assert forbidden.status_code == 403

    # Owner can create notification for a project member
    allowed = client.post(
        "/api/notifications",
        headers=owner["headers"],
        json={
            "user_id": member["id"],
            "project_id": project_id,
            "type": "invitation_sent",
            "title": "Chào mừng",
            "message": "Welcome to project",
        },
    )
    assert allowed.status_code == 201, allowed.text

    # Owner cannot target a non-member of the project
    bad_target = client.post(
        "/api/notifications",
        headers=owner["headers"],
        json={
            "user_id": outsider["id"],
            "project_id": project_id,
            "type": "invitation_sent",
            "title": "Ngoài dự án",
            "message": "Not a member",
        },
    )
    assert bad_target.status_code == 403


def test_attachment_magic_bytes_and_cleanup_on_db_error(client, test_user_factory, monkeypatch):
    owner, _, _, project_id, list_id = _setup_project_with_list(client, test_user_factory)
    task = client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={"list_id": list_id, "title": "Attachment Task"},
    ).json()
    task_id = task["id"]

    # Spoofed PNG (executable/text content claiming image/png) must be rejected
    bad_png = client.post(
        f"/api/projects/{project_id}/tasks/{task_id}/attachments",
        headers=owner["headers"],
        files={"file": ("evil.png", io.BytesIO(b"MZ_NOT_A_PNG"), "image/png")},
    )
    assert bad_png.status_code == 400

    # Valid PNG magic bytes succeeds
    valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    ok_png = client.post(
        f"/api/projects/{project_id}/tasks/{task_id}/attachments",
        headers=owner["headers"],
        files={"file": ("ok.png", io.BytesIO(valid_png_bytes), "image/png")},
    )
    assert ok_png.status_code == 201, ok_png.text
    saved_path = ok_png.json()["file_path"]
    assert os.path.exists(saved_path)
    os.remove(saved_path)

    # DB commit failure cleans up uploaded file instead of leaving orphan file
    from app.routers import attachment as attachment_router
    before_files = set(os.listdir(attachment_router.UPLOAD_DIR))

    def broken_commit(*args, **kwargs):
        raise SQLAlchemyError("simulated commit failure")

    from sqlalchemy.orm import Session
    monkeypatch.setattr(Session, "commit", broken_commit)

    with TestClient(app, raise_server_exceptions=False) as err_client:
        fail_resp = err_client.post(
            f"/api/projects/{project_id}/tasks/{task_id}/attachments",
            headers=owner["headers"],
            files={"file": ("rollback.png", io.BytesIO(valid_png_bytes), "image/png")},
        )
        assert fail_resp.status_code == 500

    after_files = set(os.listdir(attachment_router.UPLOAD_DIR))
    assert after_files == before_files


def test_websocket_rejects_revoked_or_removed_member(client, test_user_factory, monkeypatch):
    import pytest
    from starlette.websockets import WebSocketDisconnect
    from app.routers import ws as ws_router

    owner, member, outsider, project_id, _ = _setup_project_with_list(client, test_user_factory)

    # Outsider cannot connect to project WebSocket
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/ws/projects/{project_id}?token={outsider['access_token']}") as ws:
            ws.receive_json()
    assert exc_info.value.code == 1008

    # Member connects, receives initial event, then is removed via DB/API -> periodic recheck closes WS
    monkeypatch.setattr(ws_router, "WS_REVALIDATE_INTERVAL_SECONDS", 0.05)
    with client.websocket_connect(f"/api/ws/projects/{project_id}?token={member['access_token']}") as ws:
        hello = ws.receive_json()
        assert hello["event"] == "connected"

        # Remove member from project
        rm = client.delete(
            f"/api/projects/{project_id}/members/{member['id']}",
            headers=owner["headers"],
        )
        assert rm.status_code in (200, 204)

        with pytest.raises(WebSocketDisconnect) as closed_exc:
            ws.receive_json()
        assert closed_exc.value.code == 1008
