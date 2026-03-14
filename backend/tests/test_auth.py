from app.core.security import create_access_token, decode_access_token


def test_jwt_create_decode():
    token = create_access_token(subject=1)
    assert isinstance(token, str)
    sub = decode_access_token(token)
    assert sub == "1"
