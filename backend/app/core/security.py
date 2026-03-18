from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import uuid4
from jose import JWTError, jwt
from app.core.config import settings

# Single admin: JWT sub is "admin" (no user table)
ADMIN_SUB = "admin"
TOKEN_TYPE_ACCESS = "access"
ROLE_ADMIN = "admin"
ROLE_VOLUNTEER = "volunteer"


def create_access_token(
    subject: Union[str, int],
    *,
    role: str = ROLE_ADMIN,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(subject), "exp": expire, "type": TOKEN_TYPE_ACCESS, "role": role}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            return None
        sub: Optional[str] = payload.get("sub")
        return sub
    except JWTError:
        return None


def decode_access_token_payload(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            return None
        return payload
    except JWTError:
        return None


def create_volunteer_token() -> str:
    """Random token for volunteer event link (e.g. /event/:token)."""
    return uuid4().hex
