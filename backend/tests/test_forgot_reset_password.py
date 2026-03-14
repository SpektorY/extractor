"""Tests for forgot-password and reset-password flow (stub: no email sent)."""
from types import SimpleNamespace
import pytest
from tests.conftest import TestingSessionLocal
from app.models import User
from app.core.security import (
    get_password_hash,
    create_password_reset_token,
    decode_password_reset_token,
)


@pytest.fixture
def test_user(client):
    """Create a user in the test DB for password reset flow."""
    db = TestingSessionLocal()
    try:
        user = User(
            email="admin@test.com",
            hashed_password=get_password_hash("oldpass"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        yield {"email": "admin@test.com", "password": "oldpass"}
    finally:
        db.close()


def test_forgot_password_returns_200_even_for_unknown_email(client):
    """No email enumeration: always 200 and same message."""
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@test.com"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert data.get("reset_link") is None


def test_forgot_password_returns_200_for_existing_user_no_reset_link_by_default(
    client, test_user, monkeypatch
):
    """With DEBUG false, reset_link is not returned."""
    from app.core.config import settings as real_settings
    from app.api.v1.endpoints import auth as auth_endpoints

    fake_settings = SimpleNamespace(
        debug=False,
        frontend_base_url=real_settings.frontend_base_url,
    )
    monkeypatch.setattr(auth_endpoints, "settings", fake_settings)
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user["email"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("reset_link") is None


def test_forgot_password_returns_reset_link_when_debug_true(client, test_user, monkeypatch):
    """With DEBUG=true, API returns reset_link for existing user."""
    from app.core.config import settings as real_settings
    from app.api.v1.endpoints import auth as auth_endpoints

    fake_settings = SimpleNamespace(
        debug=True,
        frontend_base_url=real_settings.frontend_base_url,
    )
    monkeypatch.setattr(auth_endpoints, "settings", fake_settings)
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user["email"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("reset_link") is not None
    assert "reset-password?token=" in data["reset_link"]
    assert test_user["email"] not in data["reset_link"]  # token is JWT, not email


def test_reset_password_invalid_token_returns_400(client):
    """Invalid or expired token returns 400."""
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token", "new_password": "newpass123"},
    )
    assert r.status_code == 400


def test_reset_password_short_password_returns_400(client, test_user):
    """Password shorter than 6 characters returns 400."""
    token = create_password_reset_token(test_user["email"])
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "12345"},
    )
    assert r.status_code == 400


def test_reset_password_success_then_login(client, test_user):
    """Valid token updates password; user can log in with new password."""
    token = create_password_reset_token(test_user["email"])
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newpass123"},
    )
    assert r.status_code == 204

    # Login with old password fails
    r_login_old = client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert r_login_old.status_code == 401

    # Login with new password succeeds
    r_login_new = client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": "newpass123"},
    )
    assert r_login_new.status_code == 200
    assert "access_token" in r_login_new.json()


def test_password_reset_token_roundtrip():
    """Token encodes email and decodes correctly."""
    email = "user@example.com"
    token = create_password_reset_token(email)
    assert isinstance(token, str)
    decoded = decode_password_reset_token(token)
    assert decoded == email
