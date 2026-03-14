"""
Send transactional emails (password reset, etc.).
Supports SMTP (stdlib) and Resend API. Configure via EMAIL_BACKEND and related env vars.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_email_configured() -> bool:
    if not settings.email_backend or not settings.email_from:
        return False
    if settings.email_backend == "smtp":
        return bool(settings.smtp_host)
    if settings.email_backend == "resend":
        return bool(settings.resend_api_key)
    return False


def _send_via_smtp(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from, [to_email], msg.as_string())


def _send_via_resend(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> None:
    import resend

    resend.api_key = settings.resend_api_key
    params = {
        "from": f"{settings.email_from_name} <{settings.email_from}>",
        "to": [to_email],
        "subject": subject,
        "text": body_text,
    }
    if body_html:
        params["html"] = body_html
    resend.Emails.send(params)


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> bool:
    """
    Send an email using the configured backend (smtp or resend).
    Returns True if sent, False if email is not configured or send failed (errors are logged).
    """
    if not _is_email_configured():
        logger.debug("Email not configured (EMAIL_BACKEND/email_from not set), skip send")
        return False
    try:
        if settings.email_backend == "smtp":
            _send_via_smtp(to_email, subject, body_text, body_html)
        elif settings.email_backend == "resend":
            _send_via_resend(to_email, subject, body_text, body_html)
        else:
            logger.warning("Unknown EMAIL_BACKEND=%s", settings.email_backend)
            return False
        logger.info("Email sent to %s subject=%s", to_email, subject)
        return True
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, e)
        return False


def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Send the password reset link to the user. Safe to call from background task.
    Returns True if sent, False otherwise (caller should not expose this to client).
    """
    subject = "איפוס סיסמה — המחלץ"
    body_text = f"""שלום,

ביקשת לאפס את הסיסמה בחשבון המחלץ.

לחץ על הקישור הבא לאיפוס (תוקף שעה):

{reset_link}

אם לא ביקשת איפוס סיסמה, התעלם מהמייל.

בברכה,
צוות המחלץ
"""
    body_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="utf-8"></head>
<body>
<p>שלום,</p>
<p>ביקשת לאפס את הסיסמה בחשבון המחלץ.</p>
<p><a href="{reset_link}">לחץ כאן לאיפוס הסיסמה</a> (תוקף שעה).</p>
<p>אם לא ביקשת איפוס סיסמה, התעלם מהמייל.</p>
<p>בברכה,<br>צוות המחלץ</p>
</body>
</html>
"""
    return send_email(to_email, subject, body_text, body_html)
