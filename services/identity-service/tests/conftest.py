from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from testcontainers.redis import RedisContainer

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

os.environ.setdefault("SOMAGENT_IDENTITY_JWT_SECRET", "test-secret")

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    container = RedisContainer(image="redis:7-alpine")
    container.start()
    os.environ["SOMAGENT_IDENTITY_REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()


@pytest.fixture
def client(redis_container: RedisContainer) -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client