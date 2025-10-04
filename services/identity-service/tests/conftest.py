from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Generator

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

os.environ.setdefault("SOMAGENT_IDENTITY_JWT_SECRET", "test-secret")

from app.main import create_app  # noqa: E402


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    def _fake_from_url(url: str, **kwargs):  # noqa: ANN001
        return fake_redis

    monkeypatch.setattr("app.main.redis_from_url", _fake_from_url)
    monkeypatch.setenv("SOMAGENT_IDENTITY_JWT_SECRET", "test-secret")

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(fake_redis.flushall())
    if hasattr(fake_redis, "aclose"):
        asyncio.run(fake_redis.aclose())
    else:
        asyncio.run(fake_redis.close())