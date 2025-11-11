"""
Testing Workbench Configuration
Shared fixtures and configuration for all tests.
"""

import os
from typing import Any

import httpx
import pytest
from services.common.config.base_settings import resolve_env


@pytest.fixture(scope="session")
def test_config() -> dict[str, Any]:
"""Test configuration from environment variables."""
return {
"gateway_url": resolve_env("GATEWAY_URL", "http://localhost:10000"),
"orchestrator_url": resolve_env("ORCHESTRATOR_URL", "http://localhost:10001"),
"identity_url": resolve_env("IDENTITY_URL", "http://localhost:10002"),
"redis_url": resolve_env("REDIS_URL", "redis://localhost:10003"),
"postgres_url": resolve_env(
"POSTGRES_URL", "postgresql://somaagent:somaagent@localhost:10004/somaagent"
),
"timeout": int(resolve_env("TEST_TIMEOUT", "30")),
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
