from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.user import User


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_integer(element, compiler, **kwargs):
    return "INTEGER"


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with test_session() as db:
        db.add(
            User(
                email="admin@example.com",
                username="testadmin",
                password_hash=hash_password("AdminPass123"),
                full_name="Test Admin",
                system_role="admin",
                is_active=True,
            )
        )
        db.commit()

    try:
        # Avoid the production lifespan, which initializes the configured MySQL database.
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def register_user(client: TestClient, email: str = "member@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": "member",
            "password": "MemberPass123",
            "full_name": "Test Member",
        },
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, identifier: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_accepts_valid_user(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "username": "new_user",
            "password": "StrongPass123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert "password_hash" not in response.json()


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"username": "bad username"},
        {"password": "weak"},
    ],
    ids=["invalid-email", "invalid-username", "weak-password"],
)
def test_register_rejects_invalid_data(client: TestClient, overrides: dict):
    payload = {
        "email": "new@example.com",
        "username": "new_user",
        "password": "StrongPass123",
        "full_name": "New User",
    }
    payload.update(overrides)

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422


def test_register_rejects_duplicate_email_case_insensitively(client: TestClient):
    register_user(client)

    response = client.post(
        "/api/auth/register",
        json={
            "email": "MEMBER@example.com",
            "username": "another_user",
            "password": "StrongPass123",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize("identifier", ["member@example.com", "member"])
def test_login_accepts_email_or_username(client: TestClient, identifier: str):
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"identifier": identifier, "password": "MemberPass123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient):
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={"identifier": "member", "password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_profile_requires_authentication(client: TestClient):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_profile_returns_user_and_accepts_update(client: TestClient):
    register_user(client)
    token = login(client, "member", "MemberPass123")
    headers = {"Authorization": f"Bearer {token}"}

    profile = client.get("/api/auth/me", headers=headers)
    update = client.put(
        "/api/auth/me",
        headers=headers,
        json={"full_name": "Updated Name"},
    )

    assert profile.status_code == 200
    assert profile.json()["username"] == "member"
    assert update.status_code == 200
    assert update.json()["full_name"] == "Updated Name"


def test_profile_rejects_blank_name(client: TestClient):
    register_user(client)
    token = login(client, "member", "MemberPass123")

    response = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "   "},
    )

    assert response.status_code == 422


def test_create_project_and_list_it(client: TestClient):
    register_user(client)
    token = login(client, "member", "MemberPass123")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Release planning", "description": "First iteration"},
    )
    listed = client.get("/api/projects", headers=headers)

    assert created.status_code == 201
    assert created.json()["name"] == "Release planning"
    assert created.json()["owner_id"] == listed.json()[0]["owner_id"]
    assert len(listed.json()) == 1


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"name": "   "}, 422),
        (
            {"name": "Invalid dates", "start_date": "2026-12-10", "end_date": "2026-12-01"},
            400,
        ),
    ],
    ids=["blank-name", "end-date-before-start-date"],
)
def test_create_project_rejects_invalid_data(
    client: TestClient, payload: dict, expected_status: int
):
    token = login(client, "admin@example.com", "AdminPass123")

    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == expected_status


def test_create_project_requires_authentication(client: TestClient):
    response = client.post("/api/projects", json={"name": "Private"})

    assert response.status_code == 401


def test_admin_summary_allows_admin_only(client: TestClient):
    admin_token = login(client, "testadmin", "AdminPass123")
    member = register_user(client)
    member_token = login(client, member["username"], "MemberPass123")

    admin_response = client.get(
        "/api/admin/users/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    member_response = client.get(
        "/api/admin/users/summary",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    anonymous_response = client.get("/api/admin/users/summary")

    assert admin_response.status_code == 200
    assert admin_response.json()["user_count"] == 2
    assert member_response.status_code == 403
    assert anonymous_response.status_code == 401
