"""
Orchestrator Workflow Integration Tests
Tests Orchestrator workflow endpoints and Temporal integration.
"""

import httpx
import pytest
from services.common.config.base_settings import resolve_env


class TestOrchestratorWorkflows:
    """Integration tests for Orchestrator workflow management."""

    @pytest.mark.asyncio
    async def test_session_start_endpoint(self, http_client, test_config):
        """Test session start endpoint exists and handles requests."""
        try:
            payload = {
                "tenant": "test-tenant",
                "user": "test-user",
                "prompt": "Hello orchestrator",
                "model": "somagent-demo",
                "metadata": {"source": "integration_test"},
            }

            response = await http_client.post(
                f"{test_config['orchestrator_url']}/v1/sessions/start", json=payload
            )

            # Should return accepted or error, not 404
            assert response.status_code in [202, 400, 503]

            if response.status_code == 202:
                data = response.json()
                assert "workflow_id" in data
                assert "session_id" in data
                assert "task_queue" in data

        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")

    @pytest.mark.asyncio
    async def test_session_status_endpoint(self, http_client, test_config):
        """Test session status endpoint."""
        try:
            # Test with non-existent workflow ID
            response = await http_client.get(
                f"{test_config['orchestrator_url']}/v1/sessions/non-existent-workflow"
            )

            # Should return 404 for non-existent workflow
            assert response.status_code == 404

        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")

    @pytest.mark.asyncio
    async def test_mao_start_endpoint(self, http_client, test_config):
        """Test multi-agent orchestration start endpoint."""
        try:
            payload = {
                "tenant": "test-tenant",
                "initiator": "test-user",
                "directives": [
                    {
                        "agent_id": "test-agent",
                        "goal": "Test goal",
                        "prompt": "Test prompt",
                    }
                ],
            }

            response = await http_client.post(
                f"{test_config['orchestrator_url']}/v1/mao/start", json=payload
            )

            # Should return accepted or error, not 404
            assert response.status_code in [202, 400, 503]

            if response.status_code == 202:
                data = response.json()
                assert "workflow_id" in data
                assert "orchestration_id" in data

        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")

    @pytest.mark.asyncio
    async def test_session_validation(self, http_client, test_config):
        """Test session start validation."""
        try:
            # Missing required fields
            payload = {"prompt": "test"}

            response = await http_client.post(
                f"{test_config['orchestrator_url']}/v1/sessions/start", json=payload
            )

            # Should return validation error
            assert response.status_code == 400

        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")
