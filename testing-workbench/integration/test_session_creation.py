"""
Session Creation Integration Tests
Tests the complete session creation flow from Gateway to Orchestrator.
"""

import httpx
import pytest
from services.common.config.base_settings import resolve_env


class TestSessionCreation:
"""Integration tests for session creation workflow."""

@pytest.mark.asyncio
async def test_create_session_endpoint_exists(self, http_client, test_config):
"""Test that session creation endpoint exists and handles requests."""
try:
payload = {
"prompt": "Hello test",
"capsule_id": "demo",
"metadata": {"source": "test"},
}

response = await http_client.post(
f"{test_config['gateway_url']}/v1/sessions", json=payload
)

# Should return some response, not 404
assert response.status_code in [201, 400, 403, 502, 503]

if response.status_code == 201:
data = response.json()
assert "session_id" in data
assert "status" in data

except httpx.ConnectError:
pytest.skip("Gateway API not running")

@pytest.mark.asyncio
async def test_gateway_status_endpoint(self, http_client, test_config):
"""Test Gateway status endpoint."""
try:
response = await http_client.get(f"{test_config['gateway_url']}/v1/status")
assert response.status_code == 200
data = response.json()
assert data["service"] == "gateway"
assert data["state"] == "ready"
assert "tenant" in data
assert "client_type" in data

except httpx.ConnectError:
pytest.skip("Gateway API not running")

@pytest.mark.asyncio
async def test_session_validation(self, http_client, test_config):
"""Test session creation with invalid payload."""
try:
# Empty payload should return validation error
response = await http_client.post(
f"{test_config['gateway_url']}/v1/sessions", json={}
)

# Should return validation error, not crash
assert response.status_code in [400, 422]

except httpx.ConnectError:
pytest.skip("Gateway API not running")
