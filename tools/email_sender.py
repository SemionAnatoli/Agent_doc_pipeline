from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def _smtp_settings() -> tuple[str, int, str, str, str, bool] | None:
    host = os.getenv("SMTP_HOST", "").strip()
    port_raw = os.getenv("SMTP_PORT", "587").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or user
    use_tls = os.getenv("SMTP_USE_TLS", "1").strip() not in ("0", "false", "False")
    if not host or not sender:
        return None
    try:
        port = int(port_raw)
    except ValueError:
        return None
    return host, port, user, password, sender, use_tls


def send_document_email(recipient: str, subject: str, body: str, attachment_path: Path) -> tuple[bool, str]:
    cfg = _smtp_settings()
    if cfg is None:
        return False, "smtp_not_configured"
    host, port, user, password, sender, use_tls = cfg
    if not attachment_path.is_file():
        return False, "attachment_missing"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    data = attachment_path.read_bytes()
    msg.add_attachment(data, maintype="text", subtype="plain", filename=attachment_path.name)

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, "ok"
