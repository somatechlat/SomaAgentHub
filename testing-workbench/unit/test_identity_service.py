"""
Identity Service Unit Tests
Tests for Identity Service functionality.
"""

import httpx
import pytest


class TestIdentityService:
    """Unit tests for Identity Service."""

    @pytest.mark.asyncio
    async def test_identity_health(self, http_client, test_config):
        """Test Identity Service /health endpoint."""
        try:
            response = await http_client.get(f"{test_config['identity_url']}/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] in ["ok", "degraded"]
            assert data["service"] == "identity-service"
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")

    @pytest.mark.asyncio
    async def test_identity_ready(self, http_client, test_config):
        """Test Identity Service /ready endpoint."""
        try:
            response = await http_client.get(f"{test_config['identity_url']}/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] in ["ready", "starting"]
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")

    @pytest.mark.asyncio
    async def test_identity_root(self, http_client, test_config):
        """Test Identity Service root endpoint."""
        try:
            response = await http_client.get(f"{test_config['identity_url']}/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "SomaGent Identity Service"
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")

    @pytest.mark.asyncio
    async def test_identity_metrics(self, http_client, test_config):
        """Test Identity Service /metrics endpoint."""
        try:
            response = await http_client.get(f"{test_config['identity_url']}/metrics")
            assert response.status_code == 200
            # Should return Prometheus format metrics
            assert "# HELP" in response.text or "# TYPE" in response.text
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")
