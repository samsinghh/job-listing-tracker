"""Email notification of new listings via SMTP (Gmail-friendly).

Credentials are read from the environment, never from config or code:
    IW_SMTP_USER      SMTP login (e.g. your Gmail address)
    IW_SMTP_PASSWORD  SMTP password (for Gmail, a 16-char *App Password*)

Connection details (host/port/recipient) come from the `email:` section of
config.yaml. Defaults target Gmail's STARTTLS submission endpoint.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from .config import EmailConfig
from .models import StoredListing

ENV_USER = "IW_SMTP_USER"
ENV_PASSWORD = "IW_SMTP_PASSWORD"
ENV_TO = "IW_EMAIL_TO"  # optional override of email.to (comma-separated)


def _recipients(cfg: EmailConfig) -> list[str]:
    """Recipients, preferring the IW_EMAIL_TO env var over config.

    This lets the committed config.yaml carry only a placeholder while your
    real address stays in the gitignored .env.local.
    """
    env_to = os.environ.get(ENV_TO)
    if env_to:
        return [t.strip() for t in env_to.split(",") if t.strip()]
    return cfg.to


class NotifyError(Exception):
    """Raised when an email cannot be built or sent."""


def _format_body(listings: list[StoredListing]) -> str:
    lines = [f"{len(listings)} new internship listing(s) found:", ""]
    for item in listings:
        loc = f" — {item.location}" if item.location else ""
        lines.append(f"• [{item.company}] {item.title}{loc}")
        lines.append(f"    {item.url}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_message(
    to: list[str], sender: str, listings: list[StoredListing]
) -> EmailMessage:
    """Build the notification email. Pure (no I/O), so it is unit-testable."""
    msg = EmailMessage()
    msg["Subject"] = f"[internship-watcher] {len(listings)} new listing(s)"
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg.set_content(_format_body(listings))
    return msg


def send_new_listings(cfg: EmailConfig, listings: list[StoredListing]) -> bool:
    """Send an email about new listings. Returns True if a message was sent.

    Returns False (no-op) when there are no listings. Raises NotifyError on
    missing credentials or SMTP failure so the caller can warn without aborting
    the run.
    """
    if not listings:
        return False

    user = os.environ.get(ENV_USER)
    password = os.environ.get(ENV_PASSWORD)
    if not user or not password:
        raise NotifyError(
            f"missing credentials: set {ENV_USER} and {ENV_PASSWORD} in the environment"
        )

    recipients = _recipients(cfg)
    if not recipients:
        raise NotifyError(
            f"no recipient configured: set email.to or the {ENV_TO} env var"
        )

    sender = cfg.sender or user
    msg = build_message(recipients, sender, listings)

    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise NotifyError(f"failed to send email via {cfg.smtp_host}: {e}") from e

    return True
