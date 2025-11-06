from __future__ import annotations

import os
import sys
# Ensure sitecustomize (which patches RedisContainer) runs before importing
# testcontainers modules.
import sitecustomize  # noqa: F401
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from testcontainers.clickhouse import ClickHouseContainer
from testcontainers.redis import RedisContainer
# Ensure the required ``get_connection_url`` method exists. Some versions of
# ``testcontainers`` do not provide it, so we add a compatible implementation
# if needed.
if not hasattr(RedisContainer, "get_connection_url"):
    def _get_connection_url(self):  # pragma: no cover
        host = self.get_container_host_ip()
        port = self.get_exposed_port("6379/tcp")
        return f"redis://{host}:{port}"

    setattr(RedisContainer, "get_connection_url", _get_connection_url)
print('DEBUG: at import time, hasattr(RedisContainer, "get_connection_url") =',
    hasattr(RedisContainer, "get_connection_url"))

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
    # Debug: list attributes to verify patch applied
    print('DEBUG: RedisContainer attrs after start:', [m for m in dir(container) if not m.startswith("_")])
    if not hasattr(container, "get_connection_url"):
        print('DEBUG: get_connection_url missing')
    else:
        print('DEBUG: get_connection_url present')
    os.environ["SOMAGENT_IDENTITY_REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()


@pytest.fixture
def client(redis_container: RedisContainer, clickhouse_container: ClickHouseContainer) -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
