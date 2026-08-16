from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_login_and_me_flow(client: AsyncClient) -> None:
    register_response = await client.post(
        "/auth/register",
        json={"email": "kunin@email.com", "password": "strong-password"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "kunin@email.com"
    assert "password_hash" not in register_response.json()

    login_response = await client.post(
        "/auth/login",
        data={"username": "kunin@email.com", "password": "strong-password"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "kunin@email.com"


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(client: AsyncClient) -> None:
    payload = {"email": "kunin@email.com", "password": "strong-password"}

    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "kunin@email.com", "password": "strong-password"},
    )

    response = await client.post(
        "/auth/login",
        data={"username": "kunin@email.com", "password": "bad-password"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_or_with_invalid_token_returns_401(client: AsyncClient) -> None:
    no_token_response = await client.get("/auth/me")
    invalid_token_response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert no_token_response.status_code == 401
    assert invalid_token_response.status_code == 401
