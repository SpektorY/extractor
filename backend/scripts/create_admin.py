"""Create first admin user. Run once: python -m scripts.create_admin"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from getpass import getpass
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User


def main() -> None:
    email = input("Admin email: ").strip()
    if not email:
        print("Email required")
        sys.exit(1)
    password = getpass("Password: ")
    if not password or len(password) < 6:
        print("Password must be at least 6 characters")
        sys.exit(1)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print("User already exists")
            sys.exit(1)
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Created admin: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
