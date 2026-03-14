from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "אם החשבון קיים נשלח אימייל עם קישור לאיפוס סיסמה"
    reset_link: Optional[str] = None  # Only set when DEBUG=true (stub: no email sent)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str  # min length enforced in endpoint or validator
