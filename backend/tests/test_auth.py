import pytest
from app.core.config import Settings


def test_register_login_refresh_and_logout_with_and_without_refresh_token(client, test_user_factory):
    user = test_user_factory("auth")
    headers = user["headers"]

    # /me succeeds with valid access_token
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == user["email"]

    # Refresh token rotation works
    refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert refresh_resp.status_code == 200
    rotated = refresh_resp.json()
    new_headers = {"Authorization": f"Bearer {rotated['access_token']}"}

    # Old refresh token can no longer be reused
    reuse_resp = client.post("/api/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert reuse_resp.status_code == 401

    # Logout WITH refresh_token revokes both access and refresh tokens
    logout_resp = client.post(
        "/api/auth/logout",
        headers=new_headers,
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert logout_resp.status_code == 200

    assert client.get("/api/auth/me", headers=new_headers).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 401

    # New login -> logout WITHOUT refresh_token in body still revokes session via sid
    relogin = client.post(
        "/api/auth/login",
        json={"identifier": user["email"], "password": user["password"]},
    ).json()
    relogin_headers = {"Authorization": f"Bearer {relogin['access_token']}"}
    logout_no_ref = client.post("/api/auth/logout", headers=relogin_headers, json={})
    assert logout_no_ref.status_code == 200

    assert client.get("/api/auth/me", headers=relogin_headers).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": relogin["refresh_token"]}).status_code == 401


def test_logout_rejects_other_users_refresh_token(client, test_user_factory):
    user_a = test_user_factory("loga")
    user_b = test_user_factory("logb")

    resp = client.post(
        "/api/auth/logout",
        headers=user_a["headers"],
        json={"refresh_token": user_b["refresh_token"]},
    )
    assert resp.status_code == 403

    # User B's refresh token must remain valid
    ref_b = client.post("/api/auth/refresh", json={"refresh_token": user_b["refresh_token"]})
    assert ref_b.status_code == 200


def test_change_password_and_reset_password_invalidate_old_tokens(client, test_user_factory):
    user = test_user_factory("pwchg", password="OldPassword123!")
    old_headers = user["headers"]
    old_refresh = user["refresh_token"]

    # Change password
    chg = client.post(
        "/api/auth/me/change-password",
        headers=old_headers,
        json={"current_password": "OldPassword123!", "new_password": "NewPassword456!"},
    )
    assert chg.status_code == 200

    # Old access_token and refresh_token are both invalidated
    assert client.get("/api/auth/me", headers=old_headers).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": old_refresh}).status_code == 401

    # Old password no longer works; new password works
    assert client.post("/api/auth/login", json={"identifier": user["email"], "password": "OldPassword123!"}).status_code == 401
    login2 = client.post("/api/auth/login", json={"identifier": user["email"], "password": "NewPassword456!"})
    assert login2.status_code == 200
    tokens2 = login2.json()

    # Forgot password + Reset password also invalidates active tokens
    forgot = client.post("/api/auth/forgot-password", json={"email": user["email"]})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]

    reset = client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "new_password": "FinalPassword789!"},
    )
    assert reset.status_code == 200

    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens2['access_token']}"}).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens2["refresh_token"]}).status_code == 401
    assert client.post("/api/auth/login", json={"identifier": user["email"], "password": "FinalPassword789!"}).status_code == 200


def test_production_settings_validation_blocks_defaults():
    insecure = Settings(
        ENV="production",
        SECRET_KEY="super-secret-key",
        DB_PASSWORD="changeme",
        CORS_ORIGINS="*",
    )
    with pytest.raises(RuntimeError):
        insecure.validate_production_settings()

    assert insecure.cors_allow_credentials is False

    secure = Settings(
        ENV="production",
        SECRET_KEY="a-very-strong-random-production-secret-key-at-least-32-chars",
        DB_PASSWORD="ProdDbPassword!999",
        CORS_ORIGINS="https://app.example.com",
        FRONTEND_URL="https://app.example.com",
        SMTP_HOST="smtp.example.com",
        SMTP_FROM_EMAIL="noreply@example.com",
        PASSWORD_RESET_URL="https://app.example.com/pages/reset-password.html",
    )
    secure.validate_production_settings()
    assert secure.cors_allow_credentials is True
