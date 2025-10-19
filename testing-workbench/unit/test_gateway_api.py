"""
Gateway API Unit Tests
Tests for Gateway API service functionality.
"""

import pytest
import httpx


class TestGatewayAPI:
    """Unit tests for Gateway API service."""
    
    @pytest.mark.asyncio
    async def test_gateway_healthz(self, http_client, test_config):
        """Test Gateway /healthz endpoint."""
        try:
            response = await http_client.get(f"{test_config['gateway_url']}/healthz")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] in ["ok", "degraded"]
            assert "checks" in data
            assert "kafka" in data["checks"]
            assert "auth" in data["checks"]
            assert "redis" in data["checks"]
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")
    
    @pytest.mark.asyncio
    async def test_gateway_ready(self, http_client, test_config):
        """Test Gateway /ready endpoint."""
        try:
            response = await http_client.get(f"{test_config['gateway_url']}/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "details" in data
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")
    
    @pytest.mark.asyncio
    async def test_gateway_root(self, http_client, test_config):
        """Test Gateway root endpoint."""
        try:
            response = await http_client.get(f"{test_config['gateway_url']}/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "SomaAgentHub Service"
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")
    
    @pytest.mark.asyncio
    async def test_gateway_metrics(self, http_client, test_config):
        """Test Gateway /metrics endpoint."""
        try:
            response = await http_client.get(f"{test_config['gateway_url']}/metrics")
            assert response.status_code == 200
            # Should return Prometheus format metrics
            assert "# HELP" in response.text or "# TYPE" in response.text
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")
    
    @pytest.mark.asyncio
    async def test_list_wizards(self, http_client, test_config):
        """Test Gateway /v1/wizards endpoint."""
        try:
            response = await http_client.get(f"{test_config['gateway_url']}/v1/wizards")
            assert response.status_code == 200
            data = response.json()
            assert "wizards" in data
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")