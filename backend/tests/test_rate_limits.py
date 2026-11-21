from fastapi import Request
import pytest
from app.core.rate_limit import enforce_rate_limit, limiter
from fastapi import HTTPException

def test_login_rate_limit_is_scoped_by_ip_and_account():
    scope = {"type": "http", "headers": [], "client": ("198.51.100.9", 1234)}
    request = Request(scope)
    key = "test-login-unique@example.com"
    enforce_rate_limit(request, "test-login", key, limit=100, account_limit=1)
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(request, "test-login", key, limit=100, account_limit=1)
    assert exc.value.status_code == 429
