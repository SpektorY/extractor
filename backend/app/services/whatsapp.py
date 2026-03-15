"""WhatsApp notification service. Supports Twilio; GreenAPI can be added similarly."""
from typing import Optional
from app.core.config import settings


def send_volunteer_invite(phone: str, event_name: str, event_address: str, event_link: str) -> bool:
    """Send WhatsApp message to volunteer with event details and event link. Returns True if sent (or mocked)."""
    message = (
        f"אירוע חדש: {event_name}\n"
        f"כתובת: {event_address}\n"
        f"האם באפשרותך לסייע? לחץ על הקישור לפתיחת משימה:\n{event_link}"
    )
    provider = settings.whatsapp_provider
    if not provider:
        if settings.debug:
            print(f"[DEV] WhatsApp (no provider): to={phone} link={event_link}")
        return True
    if provider == "twilio":
        return _send_twilio(phone, message)
    if provider == "greenapi":
        return _send_greenapi(phone, message)
    return False


def _send_twilio(phone: str, body: str) -> bool:
    import logging
    log = logging.getLogger(__name__)
    try:
        from twilio.rest import Client
        if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_whatsapp_from:
            return False
        # Normalize phone: E.164 and WhatsApp prefix (required by Twilio for WhatsApp)
        number = phone if phone.startswith("+") else f"+972{phone.lstrip('0')}"
        to = number if number.startswith("whatsapp:") else f"whatsapp:{number}"
        from_raw = settings.twilio_whatsapp_from or ""
        from_number = from_raw.replace("whatsapp:", "").strip()
        # Twilio error 63031: To and From cannot be the same (e.g. volunteer is the sandbox number)
        if number == from_number or to == from_raw:
            log.info("WhatsApp skip: same To and From (volunteer number is your Twilio sender); to=%s", number)
            return False
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=settings.twilio_whatsapp_from,
            to=to,
        )
        return True
    except Exception as e:
        log.warning("Twilio WhatsApp send failed: %s", e)
        return False


def _send_greenapi(phone: str, body: str) -> bool:
    """GreenAPI: https://green-api.com/ . Implement when needed."""
    return False
