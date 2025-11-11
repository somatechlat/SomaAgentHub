from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from testcontainers.clickhouse import ClickHouseContainer
from testcontainers.redis import RedisContainer

# Ensure sitecustomize (which patches RedisContainer) runs before importing
# testcontainers modules.
import sitecustomize  # noqa: F401

print(
    'DEBUG: at import time, hasattr(RedisContainer, "get_connection_url") =',
    hasattr(RedisContainer, "get_connection_url"),
)

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

# Use the canonical prefix for the JWT secret in tests
os.environ.setdefault("SOMA_AGENT_HUB_IDENTITY_JWT_SECRET", "test-secret")

from app.main import create_app  # noqa: E402
from services.common.config.base_settings import resolve_env


@pytest.fixture(scope="session")
def clickhouse_container() -> Generator[ClickHouseContainer, None, None]:
    container = ClickHouseContainer()
    container.start()
    host = container.get_container_host_ip()
    port = container.get_exposed_port("9000/tcp")
    # Use the canonical `SOMA_AGENT_HUB_` prefix for ClickHouse configuration
    os.environ["SOMA_AGENT_HUB_CLICKHOUSE_HOST"] = host
    os.environ["SOMA_AGENT_HUB_CLICKHOUSE_PORT"] = port
    os.environ["SOMA_AGENT_HUB_CLICKHOUSE_DATABASE"] = "somastack_audit"
    os.environ["SOMA_AGENT_HUB_IDENTITY_CLICKHOUSE_HOST"] = host
    os.environ["SOMA_AGENT_HUB_IDENTITY_CLICKHOUSE_PORT"] = port
    os.environ["SOMA_AGENT_HUB_IDENTITY_CLICKHOUSE_DATABASE"] = "somastack_audit"
    yield container
    container.stop()


@pytest.fixture(scope="session")
def redis_container(
    clickhouse_container: ClickHouseContainer,
) -> Generator[RedisContainer, None, None]:
    container = RedisContainer(image="redis:7-alpine")
    container.start()
    # Debug: list attributes to verify patch applied
    print(
        "DEBUG: RedisContainer attrs after start:",
        [m for m in dir(container) if not m.startswith("_")],
    )
    if not hasattr(container, "get_connection_url"):
        print("DEBUG: get_connection_url missing")
    else:
        print("DEBUG: get_connection_url present")
    # Use the canonical prefix for Redis URL in tests
    os.environ["SOMA_AGENT_HUB_IDENTITY_REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()


@pytest.fixture
def client(
    redis_container: RedisContainer, clickhouse_container: ClickHouseContainer
) -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
