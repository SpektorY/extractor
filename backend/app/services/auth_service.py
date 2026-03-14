from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.core.security import verify_password, create_access_token


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_access_token_for_user(user: User) -> str:
    return create_access_token(subject=user.id)
