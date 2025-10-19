"""
Testing Workbench Configuration
Shared fixtures and configuration for all tests.
"""

import pytest
import httpx
import os
from typing import Dict, Any


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration from environment variables."""
    return {
        "gateway_url": os.getenv("GATEWAY_URL", "http://localhost:10000"),
        "orchestrator_url": os.getenv("ORCHESTRATOR_URL", "http://localhost:10001"),
        "identity_url": os.getenv("IDENTITY_URL", "http://localhost:10002"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:10003"),
        "postgres_url": os.getenv("POSTGRES_URL", "postgresql://somaagent:somaagent@localhost:10004/somaagent"),
        "timeout": int(os.getenv("TEST_TIMEOUT", "30")),
    }


@pytest.fixture
async def http_client():
    """Async HTTP client for API tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def service_urls(test_config):
    """Service URLs for testing."""
    return {
        "gateway": test_config["gateway_url"],
        "orchestrator": test_config["orchestrator_url"],
        "identity": test_config["identity_url"],
    }