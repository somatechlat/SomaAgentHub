from fastapi import status

from services.orchestrator.app.core.config import settings

# FIXME: These tests use FakeTemporalClient which never fails.
# They don't test real Temporal behavior (timeouts, retries, errors).
# Replace with real integration tests using docker-compose Temporal server.
# See TEST_REFACTORING_ROADMAP.md for details.


def test_session_start_initiates_temporal_workflow(api_client):
    client, fake_temporal = api_client
    payload = {
        "tenant": "tenant-123",
        "user": "user-456",
        "prompt": "hello orchestrator",
        "model": "somagent-demo",
        "metadata": {"session_id": "sess-001"},
    }

    response = client.post("/v1/sessions/start", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    expected_workflow_id = "session-sess-001"

    assert data["workflow_id"] == expected_workflow_id
    assert data["task_queue"] == settings.temporal_task_queue
    assert data["session_id"] == "sess-001"
    assert expected_workflow_id in fake_temporal.workflows


def test_session_status_returns_workflow_result(api_client):
    client, _ = api_client
    payload = {
        "tenant": "tenant-abc",
        "user": "user-def",
        "prompt": "status please",
        "metadata": {"session_id": "sess-xyz"},
    }

    start_resp = client.post("/v1/sessions/start", json=payload)
    workflow_id = start_resp.json()["workflow_id"]

    status_resp = client.get(f"/v1/sessions/{workflow_id}")
    assert status_resp.status_code == status.HTTP_200_OK
    body = status_resp.json()

    assert body["workflow_id"] == workflow_id
    assert body["status"] == "completed"
    assert body["result"] is not None
    assert body["result"]["session_id"] == "sess-xyz"


def test_session_status_not_found(api_client):
    client, _ = api_client
    resp = client.get("/v1/sessions/unknown-workflow")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_mao_start_initiates_workflow(api_client):
    client, fake_temporal = api_client
    payload = {
        "tenant": "tenant-tenant",
        "initiator": "ops",
        "directives": [
            {
                "agent_id": "research",
                "goal": "Collect intel",
                "prompt": "Aggregate insight",
                "metadata": {"model": "somagent-pro"},
            },
            {
                "agent_id": "planner",
                "goal": "Draft plan",
                "prompt": "Draft go-to-market",
            },
        ],
        "notification_channel": "ops",
    }

    response = client.post("/v1/mao/start", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    body = response.json()
    workflow_id = body["workflow_id"]
    assert workflow_id in fake_temporal.workflows
    assert body["task_queue"] == settings.temporal_task_queue


def test_mao_status_returns_result(api_client):
    client, _ = api_client
    payload = {
        "tenant": "tenant-zed",
        "initiator": "lead",
        "directives": [
            {
                "agent_id": "strategist",
                "goal": "Plan",
                "prompt": "Plan",
            }
        ],
    }

    start_resp = client.post("/v1/mao/start", json=payload)
    workflow_id = start_resp.json()["workflow_id"]

    status_resp = client.get(f"/v1/mao/{workflow_id}")
    assert status_resp.status_code == status.HTTP_200_OK
    body = status_resp.json()
    assert body["workflow_id"] == workflow_id
    assert body["result"] is not None
    assert body["result"]["status"] == "completed"
    assert body["result"]["agent_results"]
