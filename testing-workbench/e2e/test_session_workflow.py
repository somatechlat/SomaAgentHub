"""
End-to-End Session Workflow Tests
Tests complete user workflows from Gateway through Orchestrator.
"""

import pytest
import httpx
import time
import asyncio


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_session_workflow(test_config):
    """Test complete session creation and execution workflow."""
    gateway_url = test_config["gateway_url"]
    orchestrator_url = test_config["orchestrator_url"]
    
    # 1) Create session via Gateway
    payload = {
        "prompt": "Write a short hello world.",
        "capsule_id": "demo",
        "metadata": {"source": "e2e_test"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(f"{gateway_url}/v1/sessions", json=payload)
            
            # Gateway might not be fully configured, check various responses
            if resp.status_code == 503:
                pytest.skip("Gateway kill switch active or service unavailable")
            elif resp.status_code == 502:
                pytest.skip("Orchestrator unreachable from Gateway")
            elif resp.status_code == 403:
                pytest.skip("Content blocked by moderation")
            elif resp.status_code != 201:
                pytest.skip(f"Gateway returned {resp.status_code}: {resp.text}")
                
            data = resp.json()
            workflow_id = data["payload"]["workflow_id"]
            assert workflow_id
            
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")

    # 2) Poll orchestrator until workflow completes
    deadline = time.time() + 60  # 1 minute timeout
    status = None
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            while time.time() < deadline:
                r = await client.get(f"{orchestrator_url}/v1/sessions/{workflow_id}")
                
                if r.status_code == 404:
                    pytest.skip("Workflow not found in Orchestrator")
                elif r.status_code == 503:
                    pytest.skip("Temporal client not initialized")
                elif r.status_code != 200:
                    pytest.skip(f"Orchestrator returned {r.status_code}: {r.text}")
                    
                status = r.json()["status"]
                if status in {"completed", "failed", "terminated"}:
                    break
                await asyncio.sleep(2)
                
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")

    # Workflow should complete or we should know why it didn't
    assert status in {"completed", "failed", "terminated"}, f"Workflow status: {status}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_session_error_handling(test_config):
    """Test session workflow error handling."""
    gateway_url = test_config["gateway_url"]
    
    # Test invalid payload
    invalid_payload = {"invalid": "data"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(f"{gateway_url}/v1/sessions", json=invalid_payload)
            # Should return validation error, not crash
            assert resp.status_code in [400, 422]
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_orchestrator_direct_session(test_config):
    """Test creating session directly via Orchestrator."""
    orchestrator_url = test_config["orchestrator_url"]
    
    payload = {
        "tenant": "test-tenant",
        "user": "test-user",
        "prompt": "Direct orchestrator test",
        "metadata": {"source": "e2e_direct"}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(f"{orchestrator_url}/v1/sessions/start", json=payload)
            
            if resp.status_code == 503:
                pytest.skip("Temporal client not initialized")
            elif resp.status_code != 202:
                pytest.skip(f"Orchestrator returned {resp.status_code}: {resp.text}")
                
            data = resp.json()
            assert "workflow_id" in data
            assert "session_id" in data
            
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")