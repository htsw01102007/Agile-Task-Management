import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user_factory(client, db_session):
    created_emails: list[str] = []
    created_project_ids: list[int] = []

    def _create_user(prefix: str = "pytest", password: str = "StrongPass123!"):
        suffix = uuid.uuid4().hex[:8]
        email = f"{prefix}_{suffix}@example.com"
        username = f"{prefix}_{suffix}"[:40]
        reg_resp = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "full_name": f"Test {prefix} {suffix}",
            },
        )
        assert reg_resp.status_code == 201, reg_resp.text
        created_emails.append(email)

        login_resp = client.post(
            "/api/auth/login",
            json={"identifier": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        tokens = login_resp.json()
        return {
            "id": reg_resp.json()["id"],
            "email": email,
            "username": username,
            "password": password,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
        }

    def _invite_member(owner_headers: dict, project_id: int, invitee: dict, role: str = "member"):
        inv = client.post(
            f"/api/projects/{project_id}/invitations",
            headers=owner_headers,
            json={"invitee_email": invitee["email"], "role": role},
        )
        assert inv.status_code == 201, inv.text
        raw_token = inv.json()["raw_token"]
        acc = client.post(
            f"/api/invitations/accept/{raw_token}",
            headers=invitee["headers"],
        )
        assert acc.status_code == 200, acc.text

    _create_user.track_project = lambda pid: created_project_ids.append(pid)
    _create_user.invite_member = _invite_member
    yield _create_user

    # Cleanup created projects and users
    db = SessionLocal()
    try:
        if created_project_ids:
            db.query(Project).filter(Project.id.in_(created_project_ids)).delete(synchronize_session=False)
            db.commit()
        if created_emails:
            db.query(User).filter(User.email.in_(created_emails)).delete(synchronize_session=False)
            db.commit()
    finally:
        db.close()

