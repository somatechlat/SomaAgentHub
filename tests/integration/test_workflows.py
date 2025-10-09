"""
Integration tests for Temporal workflows.
Sprint-5: Test KAMACHIQ autonomous orchestration.
"""

import pytest
from datetime import timedelta
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
import os
import httpx

WORKFLOWS_AVAILABLE = True
try:
    from workflows import (
        KAMACHIQProjectWorkflow,
        AgentTaskWorkflow,
        decompose_project,
        create_task_plan,
        spawn_agent,
        execute_task,
        review_output,
        aggregate_results,
    )
except Exception:
    WORKFLOWS_AVAILABLE = False


@pytest.fixture
async def workflow_environment():
    """Create test Temporal environment."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env


@pytest.fixture
async def worker(workflow_environment):
    """Create test worker."""
    if not WORKFLOWS_AVAILABLE:
        pytest.skip("Internal workflows module not available in import path")
    async with Worker(
        workflow_environment.client,
        task_queue="test-queue",
        workflows=[KAMACHIQProjectWorkflow, AgentTaskWorkflow],
        activities=[
            decompose_project,
            create_task_plan,
            spawn_agent,
            execute_task,
            review_output,
            aggregate_results,
        ],
    ):
        yield


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_kamachiq_workflow_simple_project(workflow_environment, worker):
    """Test KAMACHIQ workflow with simple project."""
    
    result = await workflow_environment.client.execute_workflow(
        KAMACHIQProjectWorkflow.run,
        args=[
            "Create a Python script that prints Hello World",
            "test_user",
            "test_session_001"
        ],
        id="test-workflow-001",
        task_queue="test-queue",
        execution_timeout=timedelta(minutes=5),
    )
    
    assert result is not None
    assert result["status"] == "completed"
    assert result["task_count"] > 0
    assert result["quality_score"] >= 0.0
    assert result["quality_score"] <= 1.0


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_agent_task_workflow(workflow_environment, worker):
    """Test individual agent task workflow."""
    
    task = {
        "id": "task_001",
        "name": "Write hello world function",
        "description": "Create a function that returns 'Hello World'",
        "type": "code",
        "dependencies": []
    }
    
    agent = {
        "agent_id": "agent_test_001",
        "capabilities": ["python", "coding"]
    }
    
    result = await workflow_environment.client.execute_workflow(
        AgentTaskWorkflow.run,
        args=[task, agent, "test_user"],
        id="test-agent-workflow-001",
        task_queue="test-queue",
        execution_timeout=timedelta(minutes=2),
    )
    
    assert result is not None
    assert result["task_id"] == "task_001"
    assert "output" in result
    assert result["status"] in ["completed", "failed"]


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_decompose_project_activity():
    """Test project decomposition activity."""
    
    result = await decompose_project(
        "Build a calculator CLI with add, subtract, multiply, divide operations",
        "test_user"
    )
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    for task in result:
        assert "id" in task
        assert "name" in task
        assert "description" in task
        assert "type" in task
        assert "dependencies" in task


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_create_task_plan_activity():
    """Test task planning activity."""
    
    tasks = [
        {"id": "task_1", "name": "Setup", "dependencies": []},
        {"id": "task_2", "name": "Implement", "dependencies": ["task_1"]},
        {"id": "task_3", "name": "Test", "dependencies": ["task_2"]},
    ]
    
    result = await create_task_plan(tasks)
    
    assert "waves" in result
    assert len(result["waves"]) > 0
    
    # task_1 should be in wave 0 (no dependencies)
    assert "task_1" in [t["id"] for t in result["waves"][0]]
    
    # task_2 should be in wave 1 (depends on task_1)
    assert "task_2" in [t["id"] for t in result["waves"][1]]


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_spawn_agent_activity():
    """Test agent spawning activity."""
    
    task = {
        "id": "task_001",
        "name": "Test task",
        "type": "code"
    }
    
    result = await spawn_agent(task, "test_user")
    
    assert "agent_id" in result
    assert "capabilities" in result
    assert "spawned_at" in result
    assert result["task_id"] == "task_001"


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_review_output_activity():
    """Test output review activity."""
    
    outputs = [
        {
            "task_id": "task_1",
            "output": "Successfully completed task 1",
            "quality_metrics": {"coherence": 0.9, "completeness": 0.85}
        },
        {
            "task_id": "task_2",
            "output": "Successfully completed task 2",
            "quality_metrics": {"coherence": 0.95, "completeness": 0.90}
        },
    ]
    
    result = await review_output(outputs, "test_project")
    
    assert "approved" in result
    assert "quality_score" in result
    assert isinstance(result["approved"], bool)
    assert 0.0 <= result["quality_score"] <= 1.0


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_aggregate_results_activity():
    """Test results aggregation activity."""
    
    outputs = [
        {
            "task_id": "task_1",
            "output": "Result 1",
            "execution_time_ms": 1000,
            "tokens_used": 500
        },
        {
            "task_id": "task_2",
            "output": "Result 2",
            "execution_time_ms": 1500,
            "tokens_used": 750
        },
    ]
    
    result = await aggregate_results(outputs)
    
    assert "project_id" in result
    assert "task_count" in result
    assert "total_execution_time_ms" in result
    assert "total_tokens_used" in result
    
    assert result["task_count"] == 2
    assert result["total_execution_time_ms"] == 2500
    assert result["total_tokens_used"] == 1250


@pytest.mark.asyncio
@pytest.mark.skipif(not WORKFLOWS_AVAILABLE, reason="Internal workflows module not available")
async def test_workflow_with_quality_failure(workflow_environment, worker):
    """Test workflow handles quality gate failures."""
    
    # This would need mock activities that return low quality scores
    # For now, test that workflow completes even with failures
    
    result = await workflow_environment.client.execute_workflow(
        KAMACHIQProjectWorkflow.run,
        args=[
            "Invalid or problematic project description",
            "test_user",
            "test_session_002"
        ],
        id="test-workflow-002",
        task_queue="test-queue",
        execution_timeout=timedelta(minutes=5),
    )
    
    assert result is not None
    # Should complete but may have status other than "completed"
    assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


@pytest.mark.asyncio
async def test_start_session_via_gateway():
    """Start a real session via Gateway -> Orchestrator without mocks.

    Requires a running Gateway service (and Orchestrator) reachable at E2E_GATEWAY_URL or localhost:8080.
    """
    gateway_url = os.getenv("E2E_GATEWAY_URL", "http://localhost:8080")
    payload = {
        "prompt": "Say hello to the world",
        "capsule_id": "demo",
        "metadata": {"source": "integration"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{gateway_url}/v1/sessions", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data.get("status", "accepted") in {"accepted", "created"}
        assert "payload" in data and "workflow_id" in data["payload"]
