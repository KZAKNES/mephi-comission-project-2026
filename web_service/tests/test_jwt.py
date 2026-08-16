from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import decode_and_validate


def make_token(subject: str = "42", role: str = "user") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": subject,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def test_decode_and_validate_returns_payload() -> None:
    token = make_token(subject="123")

    payload = decode_and_validate(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "user"


def test_decode_and_validate_rejects_garbage_token() -> None:
    with pytest.raises(ValueError):
        decode_and_validate("not-a-jwt")
