"""
Orchestrator Unit Tests
Tests for Orchestrator service functionality.
"""

import pytest
import httpx


class TestOrchestrator:
    """Unit tests for Orchestrator service."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_health(self, http_client, test_config):
        """Test Orchestrator /health endpoint."""
        try:
            response = await http_client.get(f"{test_config['orchestrator_url']}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "orchestrator"
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_orchestrator_ready(self, http_client, test_config):
        """Test Orchestrator /ready endpoint."""
        try:
            response = await http_client.get(f"{test_config['orchestrator_url']}/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] in ["ready", "starting"]
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_orchestrator_root(self, http_client, test_config):
        """Test Orchestrator root endpoint."""
        try:
            response = await http_client.get(f"{test_config['orchestrator_url']}/")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "SomaGent Orchestrator Service"
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
    
    @pytest.mark.asyncio
    async def test_orchestrator_metrics(self, http_client, test_config):
        """Test Orchestrator /metrics endpoint."""
        try:
            response = await http_client.get(f"{test_config['orchestrator_url']}/metrics")
            assert response.status_code == 200
            # Should return Prometheus format metrics
            assert "# HELP" in response.text or "# TYPE" in response.text
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")