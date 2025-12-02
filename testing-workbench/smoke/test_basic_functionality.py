"""
Basic Functionality Smoke Tests
Quick tests to verify core functionality is working.
"""

import httpx
import pytest
from services.common.config.base_settings import resolve_env


class TestBasicFunctionality:
        """Basic smoke tests for core functionality."""

        @pytest.mark.asyncio
    async def test_gateway_accepts_requests(self, http_client, test_config):
                """Test that Gateway accepts and processes requests."""
                try:
        # Test healthz endpoint
                    response = await http_client.get(f"{test_config['gateway_url']}/healthz")
                    assert response.status_code == 200

                    data = response.json()
                    assert isinstance(data, dict)
                    assert "status" in data
                    assert "checks" in data

                    except httpx.ConnectError:
                        pytest.skip("Gateway not running")

                        @pytest.mark.asyncio
    async def test_orchestrator_temporal_readiness(self, http_client, test_config):
                            """Test that Orchestrator reports readiness status."""
                            try:
                                response = await http_client.get(f"{test_config['orchestrator_url']}/ready")
                                assert response.status_code == 200

                                data = response.json()
                                assert "status" in data
        # Status should be "ready" or "starting"
                                assert data["status"] in ["ready", "starting"]

                                except httpx.ConnectError:
                                    pytest.skip("Orchestrator not running")

                                    @pytest.mark.asyncio
    async def test_identity_service_basic_endpoints(self, http_client, test_config):
                                        """Test that Identity Service basic endpoints work."""
                                        try:
        # Test health endpoint
                                            response = await http_client.get(f"{test_config['identity_url']}/health")
                                            assert response.status_code == 200

                                            data = response.json()
                                            assert "status" in data
                                            assert "service" in data
                                            assert data["service"] == "identity-service"

                                            except httpx.ConnectError:
                                                pytest.skip("Identity Service not running")

                                                @pytest.mark.asyncio
    async def test_service_root_endpoints(self, http_client, test_config):
                                                    """Test that services have working root endpoints."""
                                                    services = [
                                                    (test_config["gateway_url"], "SomaAgentHub Service"),
                                                    (test_config["orchestrator_url"], "SomaGent Orchestrator Service"),
                                                    (test_config["identity_url"], "SomaGent Identity Service"),
                                                    ]

                                                    working_services = 0
                                                    for service_url, expected_message in services:
                                                        try:
                                                            response = await http_client.get(f"{service_url}/")
                                                            if response.status_code == 200:
            data = response.json()
            if data.get("message") == expected_message:
                working_services += 1
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass

        # At least one service should have working root endpoint
                    assert working_services > 0, f"Working services: {working_services}/3"
