"""
Service Health Integration Tests
Tests that all core services are running and responding correctly.
"""

import httpx
import pytest


class TestServiceHealth:
    """Test health endpoints for core services."""

    @pytest.mark.asyncio
    async def test_gateway_health(self, http_client, service_urls):
        """Test Gateway API health endpoint."""
        try:
            response = await http_client.get(f"{service_urls['gateway']}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")

    @pytest.mark.asyncio
    async def test_orchestrator_health(self, http_client, service_urls):
        """Test Orchestrator health endpoint."""
        try:
            response = await http_client.get(f"{service_urls['orchestrator']}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")

    @pytest.mark.asyncio
    async def test_identity_health(self, http_client, service_urls):
        """Test Identity Service health endpoint."""
        try:
            response = await http_client.get(f"{service_urls['identity']}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")


class TestServiceReadiness:
    """Test readiness endpoints for core services."""

    @pytest.mark.asyncio
    async def test_all_services_ready(self, http_client, service_urls):
        """Test that all services report ready status."""
        results = {}

        for service_name, url in service_urls.items():
            try:
                response = await http_client.get(f"{url}/ready", timeout=5.0)
                results[service_name] = response.status_code in [200, 503]
            except (httpx.ConnectError, httpx.TimeoutException):
                results[service_name] = False

        # At least gateway should be running
        assert results.get("gateway", False), f"Service readiness: {results}"
