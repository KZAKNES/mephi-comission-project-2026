from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import settings
from app.main import app
from app.api import routes_web


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


@pytest.fixture
async def client(fake_redis, monkeypatch, mocker) -> AsyncClient:
    monkeypatch.setattr("app.main.get_redis", lambda: fake_redis)
    delay_mock = mocker.patch.object(routes_web.llm_request, "delay")
    delay_mock.return_value.id = "task-1"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_index_renders_form(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "LLM Consultation" in response.text
    assert 'name="token"' in response.text


@pytest.mark.asyncio
async def test_token_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/token",
        data={"token": "bad-token"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Token is invalid or expired" in response.text


@pytest.mark.asyncio
async def test_token_is_saved_in_redis(
    client: AsyncClient,
    fake_redis,
) -> None:
    token = make_token()

    response = await client.post(
        "/token",
        data={"token": token},
    )

    assert response.status_code == 303
    keys = await fake_redis.keys("session:*:jwt")
    assert len(keys) == 1
    assert await fake_redis.get(keys[0]) == token


@pytest.mark.asyncio
async def test_ask_requires_saved_token(client: AsyncClient) -> None:
    response = await client.post(
        "/ask",
        data={"prompt": "Question?"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Save a JWT before asking the model" in response.text


@pytest.mark.asyncio
async def test_ask_with_saved_token_queues_task(client: AsyncClient) -> None:
    token = make_token(subject="42")
    token_response = await client.post("/token", data={"token": token})
    cookie = token_response.headers["set-cookie"].split(";", 1)[0]

    response = await client.post(
        "/ask",
        data={"prompt": "Question?"},
        headers={"Cookie": cookie},
    )

    assert response.status_code == 303
    assert "task_id=task-1" in response.headers["location"]
    routes_web.llm_request.delay.assert_called_once_with("Question?")
