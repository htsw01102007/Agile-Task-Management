from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from app.core.rate_limit import InMemoryRateLimiter
from app.core.time import as_utc_naive, utc_now_naive

def test_rate_limiter_rejects_requests_over_limit():
    limiter = InMemoryRateLimiter()
    limiter.check("login:ip:127.0.0.1", limit=2, window_seconds=60)
    limiter.check("login:ip:127.0.0.1", limit=2, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        limiter.check("login:ip:127.0.0.1", limit=2, window_seconds=60)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers

def test_datetime_normalizes_timezone_to_utc_naive_for_dst_boundaries():
    # DST transition offset is applied before storage; stored value is always UTC naive.
    local = datetime(2024, 3, 10, 3, 30, tzinfo=timezone(timedelta(hours=-4)))
    assert as_utc_naive(local) == datetime(2024, 3, 10, 7, 30)
    naive = datetime(2024, 11, 3, 1, 30)
    assert as_utc_naive(naive) == naive
    assert utc_now_naive().tzinfo is None

def test_reset_password_sends_message_and_returns_only_generic_response(client, test_user_factory, monkeypatch):
    from app.crud import auth as auth_crud
    user = test_user_factory("resetmail")
    sent = []
    monkeypatch.setattr(auth_crud, "send_password_reset_email", lambda email, token: sent.append((email, token)))

    response = client.post("/api/auth/forgot-password", json={"email": user["email"]})
    missing = client.post("/api/auth/forgot-password", json={"email": "missing@example.com"})

    assert response.status_code == 200
    assert missing.status_code == 200
    assert response.json()["message"] == missing.json()["message"]
    assert sent and sent[0][0] == user["email"]
    assert response.json()["reset_token"]
