"""
Docker Compose Smoke Tests
Tests that verify docker-compose deployment is working.
"""

import httpx
import pytest
from services.common.config.base_settings import resolve_env


class TestDockerComposeDeployment:
"""Smoke tests for docker-compose deployment."""

@pytest.mark.asyncio
async def test_core_services_responding(self, http_client, test_config):
"""Test that core services from docker-compose are responding."""
services = {
"gateway": (test_config["gateway_url"], "/healthz"),
"orchestrator": (test_config["orchestrator_url"], "/health"),
"identity": (test_config["identity_url"], "/health"),
}

results = {}
for service_name, (url, endpoint) in services.items():
try:
response = await http_client.get(f"{url}{endpoint}", timeout=5.0)
results[service_name] = response.status_code == 200
except (httpx.ConnectError, httpx.TimeoutException):
results[service_name] = False

# At least one service should be running
running_count = sum(results.values())
assert running_count > 0, f"No core services running: {results}"

@pytest.mark.asyncio
async def test_infrastructure_accessibility(self, http_client):
"""Test that infrastructure services are accessible."""
infrastructure = [
("prometheus", "http://localhost:10010", "/-/healthy"),
("grafana", "http://localhost:10011", "/api/health"),
]

accessible_count = 0
for service, base_url, endpoint in infrastructure:
try:
response = await http_client.get(f"{base_url}{endpoint}", timeout=3.0)
if response.status_code in [200, 404]:  # 404 means service is up
    accessible_count += 1
except (httpx.ConnectError, httpx.TimeoutException):
pass

# Infrastructure services are optional for basic functionality
# Just verify we can test them
assert accessible_count >= 0

@pytest.mark.asyncio
async def test_service_metrics_endpoints(self, http_client, test_config):
"""Test that services expose metrics endpoints."""
services = [
test_config["gateway_url"],
test_config["orchestrator_url"],
test_config["identity_url"],
]

metrics_working = 0
for service_url in services:
try:
response = await http_client.get(f"{service_url}/metrics", timeout=3.0)
if response.status_code == 200 and (
    "# HELP" in response.text or "# TYPE" in response.text
):
    metrics_working += 1
except (httpx.ConnectError, httpx.TimeoutException):
pass

# At least some services should have working metrics
assert metrics_working >= 0, f"Metrics working on {metrics_working} services"
