from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import uuid4
from jose import JWTError, jwt
from app.core.config import settings

# Single admin: JWT sub is "admin" (no user table)
ADMIN_SUB = "admin"


def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            return None
        sub: Optional[str] = payload.get("sub")
        return sub
    except JWTError:
        return None


def create_volunteer_token() -> str:
    """Random token for volunteer event link (e.g. /event/:token)."""
    return uuid4().hex
