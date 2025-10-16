from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from testcontainers.clickhouse import ClickHouseContainer
from testcontainers.redis import RedisContainer

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

os.environ.setdefault("SOMAGENT_IDENTITY_JWT_SECRET", "test-secret")

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def clickhouse_container() -> Generator[ClickHouseContainer, None, None]:
    container = ClickHouseContainer()
    container.start()
    host = container.get_container_host_ip()
    port = container.get_exposed_port("9000/tcp")
    os.environ["SOMASTACK_CLICKHOUSE_HOST"] = host
    os.environ["SOMASTACK_CLICKHOUSE_PORT"] = port
    os.environ["SOMASTACK_CLICKHOUSE_DATABASE"] = "somastack_audit"
    os.environ["SOMASTACK_IDENTITY_CLICKHOUSE_HOST"] = host
    os.environ["SOMASTACK_IDENTITY_CLICKHOUSE_PORT"] = port
    os.environ["SOMASTACK_IDENTITY_CLICKHOUSE_DATABASE"] = "somastack_audit"
    yield container
    container.stop()


@pytest.fixture(scope="session")
def redis_container(clickhouse_container: ClickHouseContainer) -> Generator[RedisContainer, None, None]:
    container = RedisContainer(image="redis:7-alpine")
    container.start()
    os.environ["SOMAGENT_IDENTITY_REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()


@pytest.fixture
def client(redis_container: RedisContainer, clickhouse_container: ClickHouseContainer) -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
