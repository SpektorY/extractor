from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, ADMIN_SUB
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
    sub = decode_access_token(credentials.credentials)
    if sub != ADMIN_SUB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן לא תקין או שפג תוקפו",
        )
    return AdminAuth()
