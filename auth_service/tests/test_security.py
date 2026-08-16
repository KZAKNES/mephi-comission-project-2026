from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_password_and_verify_password() -> None:
    password = "very-secret-password"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_create_access_token_contains_required_claims() -> None:
    token = create_access_token(subject="42", role="admin")

    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert "iat" in payload
    assert "exp" in payload
