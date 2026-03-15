from app.core.security import create_access_token, decode_access_token, ADMIN_SUB


def test_jwt_create_decode():
    token = create_access_token(subject=ADMIN_SUB)
    assert isinstance(token, str)
    sub = decode_access_token(token)
    assert sub == ADMIN_SUB


def test_login_wrong_password(client):
    r = client.post("/api/v1/auth/login", json={"password": "wrong"})
    assert r.status_code == 401


def test_login_success(client):
    r = client.post("/api/v1/auth/login", json={"password": "test-admin-pass"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"
