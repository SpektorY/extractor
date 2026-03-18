"""SMS delivery utilities for OTP and approval notifications."""

from app.core.config import settings


def _digits_only(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def normalize_phone_for_storage(phone: str) -> str:
    """
    Normalize Israeli phone to local canonical form: 0XXXXXXXXX.
    Accepts variants like +972523722394, 972523722394, 523762294, 052-322-9394.
    """
    digits = _digits_only(phone)
    if not digits:
        raise ValueError("נא להזין טלפון")
    if digits.startswith("972"):
        digits = digits[3:]
    if len(digits) == 9:
        digits = f"0{digits}"
    if len(digits) != 10 or not digits.startswith("0"):
        raise ValueError("מספר טלפון לא תקין")
    return digits


def normalize_phone_to_e164(phone: str) -> str:
    local = normalize_phone_for_storage(phone)
    return f"+972{local[1:]}"


def send_sms(phone: str, body: str) -> bool:
    """Send SMS via Twilio. Returns False when provider is not configured."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_sms_from:
        if settings.debug:
            print(f"[DEV] SMS skip (missing Twilio config): to={phone} body={body}")
        return False
    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=settings.twilio_sms_from,
            to=normalize_phone_to_e164(phone),
        )
        return True
    except Exception:
        return False


def send_otp_sms(phone: str, code: str) -> bool:
    return send_sms(phone, f"קוד ההתחברות שלך הוא: {code}")


def send_approved_sms(phone: str) -> bool:
    return send_sms(phone, "אושרת! אפשר להמשיך לאירוע.")
