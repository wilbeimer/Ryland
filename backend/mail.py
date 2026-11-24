import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Literal

logger = logging.getLogger(__name__)


def send_verification_email(
    to_email: str, verify_url: str
) -> Literal["sent", "logged"]:
    """Email a verification link using stdlib SMTP.

    Returns ``sent`` when the message is handed to the server. When
    ``SMTP_HOST`` or a From address is unset, or the send fails, the link is
    printed to the console and this returns ``logged`` so local dev works
    without credentials.
    """
    host = os.getenv("SMTP_HOST", "").strip()
    sender = os.getenv("SMTP_FROM", "").strip() or os.getenv("SMTP_USER", "").strip()
    if not host or not sender:
        _log_link(to_email, verify_url)
        return "logged"

    message = EmailMessage()
    message["Subject"] = "Verify your Ryland account"
    message["From"] = sender
    message["To"] = to_email
    message.set_content(
        "Confirm your Ryland account by opening this link:\n\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours. "
        "If you did not create an account, you can ignore this email.\n"
    )
    try:
        _smtp_send(host, _smtp_port(), sender, message)
    except Exception:
        logger.exception("SMTP send failed for %s", to_email)
        _log_link(to_email, verify_url)
        return "logged"
    return "sent"


def _log_link(to_email: str, verify_url: str) -> None:
    # Printed, not only logged: uvicorn's default config does not always
    # show this module's logger, and local dev needs the link on the console.
    print(
        f"Ryland verification link for {to_email}: {verify_url}",
        flush=True,
    )


def _smtp_port() -> int:
    raw = os.getenv("SMTP_PORT", "587").strip() or "587"
    try:
        return int(raw)
    except ValueError:
        return 587


def _smtp_send(host: str, port: int, sender: str, message: EmailMessage) -> None:
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
        return
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(message, from_addr=sender)
