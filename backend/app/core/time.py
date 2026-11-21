from datetime import datetime, timezone

def utc_now_naive() -> datetime:
    # UTC now represented without tzinfo for timezone-naive DATETIME columns.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc_naive(value: datetime | None) -> datetime | None:
    # Existing naive inputs are interpreted as UTC for backwards compatibility.
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
