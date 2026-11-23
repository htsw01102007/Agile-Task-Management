"""Kiểm tra email trước khi đăng ký.

Chấp nhận email khi:
- đúng định dạng
- tên miền có bản ghi MX (nhận được thư)
- không thuộc tên miền thư tạm / thư ảo đã biết

Không dò hộp thư bằng SMTP: cách đó hay bị máy chủ thư chặn và không đáng tin.
"""
from email_validator import EmailNotValidError, EmailUndeliverableError, validate_email

DISPOSABLE_DOMAINS = frozenset(
    {
        "10minutemail.com",
        "10minutemail.net",
        "burnermail.io",
        "dispostable.com",
        "discard.email",
        "emailondeck.com",
        "fakeinbox.com",
        "getairmail.com",
        "getnada.com",
        "grr.la",
        "guerrillamail.biz",
        "guerrillamail.com",
        "guerrillamail.de",
        "guerrillamail.info",
        "guerrillamail.net",
        "guerrillamail.org",
        "guerrillamailblock.com",
        "inboxkitten.com",
        "mailinator.com",
        "mailnesia.com",
        "maildrop.cc",
        "mintemail.com",
        "mohmal.com",
        "mytemp.email",
        "pokemail.net",
        "sharklasers.com",
        "spam4.me",
        "spamgourmet.com",
        "temp-mail.io",
        "temp-mail.org",
        "tempail.com",
        "tempmail.com",
        "tempmail.net",
        "throwawaymail.com",
        "trash-mail.com",
        "trashmail.com",
        "yopmail.com",
        "yopmail.fr",
        "yopmail.net",
    }
)


class EmailRejectedError(ValueError):
    pass


def is_disposable_domain(domain: str) -> bool:
    labels = domain.lower().strip(".").split(".")
    for index in range(len(labels) - 1):
        if ".".join(labels[index:]) in DISPOSABLE_DOMAINS:
            return True
    return False


def normalize_email_syntax(value: str) -> str:
    """Chuẩn hoá email lúc đăng nhập. Không kiểm tra MX, để tài khoản đã có vẫn đăng nhập được."""
    try:
        result = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as error:
        raise EmailRejectedError("Email không đúng định dạng") from error
    return result.normalized.lower()


def normalize_real_email(value: str) -> str:
    raw = value.strip()
    domain = raw.rsplit("@", 1)[-1].lower() if "@" in raw else ""
    if domain and is_disposable_domain(domain):
        raise EmailRejectedError("Không chấp nhận email tạm thời hoặc email ảo")

    try:
        result = validate_email(raw, check_deliverability=True)
    except EmailUndeliverableError as error:
        raise EmailRejectedError(
            "Tên miền email không tồn tại hoặc không nhận được thư"
        ) from error
    except EmailNotValidError as error:
        raise EmailRejectedError("Email không đúng định dạng") from error

    normalized = result.normalized.lower()
    normalized_domain = normalized.rsplit("@", 1)[-1]
    if is_disposable_domain(normalized_domain):
        raise EmailRejectedError("Không chấp nhận email tạm thời hoặc email ảo")
    return normalized
