from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    decode_access_token,
    decode_password_reset_token,
    create_password_reset_token,
    get_password_hash,
)
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import authenticate_user, create_access_token_for_user
from app.services.email_service import send_password_reset_email

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="אימייל או סיסמה שגויים",
        )
    token = create_access_token_for_user(user)
    return TokenResponse(access_token=token)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="חסר טוקן או טוקן לא תקין",
        )
    sub = decode_access_token(credentials.credentials)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="טוקן לא תקין או שפג תוקפו",
        )
    try:
        user_id = int(sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="טוקן לא תקין")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="משתמש לא פעיל")
    return user


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    background_tasks: BackgroundTasks,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    user = db.query(User).filter(User.email == body.email).first()
    reset_link = None
    if user:
        token = create_password_reset_token(user.email)
        reset_link = f"{settings.frontend_base_url}/reset-password?token={token}"
        # Send email in background when email is configured (smtp/resend)
        background_tasks.add_task(send_password_reset_email, user.email, reset_link)
        if settings.debug:
            print(f"[DEV] Password reset link for {user.email}: {reset_link}")
    return ForgotPasswordResponse(reset_link=reset_link if settings.debug else None)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> None:
    email = decode_password_reset_token(body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="קישור לאיפוס סיסמה לא תקין או שפג תוקפו",
        )
    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="הסיסמה חייבת להכיל לפחות 6 תווים",
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="משתמש לא נמצא")
    user.hashed_password = get_password_hash(body.new_password)
    db.commit()
    return None
