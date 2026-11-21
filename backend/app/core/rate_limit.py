from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from fastapi import HTTPException, Request, status
class InMemoryRateLimiter:
    # Process-local window; deployment with multiple workers should use shared storage.
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Bạn thao tác quá nhanh. Vui lòng thử lại sau.",
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)

limiter = InMemoryRateLimiter()


def enforce_rate_limit(
    request: Request,
    action: str,
    account: str | None = None,
    limit: int = 10,
    window_seconds: int = 60,
    account_limit: int | None = None,
    ip_limit: int | None = None,
) -> None:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    client_ip = forwarded_for or (request.client.host if request.client else "unknown")
    limiter.check(f"{action}:ip:{client_ip}", ip_limit if ip_limit is not None else limit, window_seconds)
    if account:
        limiter.check(
            f"{action}:account:{account.strip().lower()}",
            account_limit if account_limit is not None else limit,
            window_seconds,
        )
