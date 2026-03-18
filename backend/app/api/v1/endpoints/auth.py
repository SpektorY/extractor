from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token_payload,
    ADMIN_SUB,
    ROLE_ADMIN,
    ROLE_VOLUNTEER,
)
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()
security = HTTPBearer(auto_error=False)


class AdminAuth:
    """Sentinel for authenticated admin (no user table)."""

    pass


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    if not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="מנהל לא הוגדר. הגדר ADMIN_PASSWORD ב-.env",
        )
    if body.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="סיסמה שגויה",
        )
    token = create_access_token(subject=ADMIN_SUB)
    return TokenResponse(access_token=token)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AdminAuth:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="חסר טוקן או טוקן לא תקין",
        )
    payload = decode_access_token_payload(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן לא תקין או שפג תוקפו",
        )
    sub = payload.get("sub")
    role = payload.get("role")
    if sub != ADMIN_SUB or (role and role != ROLE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן לא תקין או שפג תוקפו",
        )
    return AdminAuth()


class VolunteerAuth:
    def __init__(self, volunteer_id: int):
        self.volunteer_id = volunteer_id


def get_optional_current_volunteer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[VolunteerAuth]:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    payload = decode_access_token_payload(credentials.credentials)
    if not payload:
        return None
    if payload.get("role") != ROLE_VOLUNTEER:
        return None
    try:
        volunteer_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    return VolunteerAuth(volunteer_id=volunteer_id)
