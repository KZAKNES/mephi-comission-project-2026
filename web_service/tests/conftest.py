import pytest
from fakeredis.aioredis import FakeRedis


@pytest.fixture
async def fake_redis() -> FakeRedis:
    redis = FakeRedis(decode_responses=True)
    try:
        yield redis
    finally:
        await redis.aclose()
