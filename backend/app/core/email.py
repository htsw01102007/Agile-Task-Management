import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote
from app.core.config import settings
logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, raw_token: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL or not settings.PASSWORD_RESET_URL:
        if settings.ENV.strip().lower() == "development":
            logger.warning("SMTP is not configured; password reset email was not sent for %s", email)
            return
        raise RuntimeError("Email delivery is not configured")

    reset_url = settings.PASSWORD_RESET_URL
    separator = "&" if "?" in reset_url else "?"
    reset_url = f"{reset_url}{separator}token={quote(raw_token)}"
    message = EmailMessage()
    message["Subject"] = "Hướng dẫn đặt lại mật khẩu Agile Workspace"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.\n\n"
        f"Mở liên kết sau để đặt mật khẩu mới (có hiệu lực {settings.PASSWORD_RESET_EXPIRE_MINUTES} phút):\n"
        f"{reset_url}\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
