from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("iarh.email")


def send_email(*, recipient: str, subject: str, body: str) -> None:
    settings = get_settings()
    if settings.email_delivery_mode != "smtp":
        raise RuntimeError("EMAIL_DELIVERY_NOT_CONFIGURED")
    if not settings.smtp_host or not settings.email_from:
        raise RuntimeError("SMTP_NOT_CONFIGURED")

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)
