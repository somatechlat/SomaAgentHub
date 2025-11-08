from fastapi import status


def test_capsule_run_starts_workflow(api_client):
    client, fake_temporal = api_client

    payload = {
        "tenant": "tenant-x",
        "user": "user-y",
        "capsule_id": "org/demo",
        "version": "1.2.3",
        "params": {"alpha": 1},
        "metadata": {"run_id": "run-123"},
    }

    resp = client.post("/v1/capsule/run", json=payload)
    assert resp.status_code == status.HTTP_202_ACCEPTED
    data = resp.json()

    # Basic shape
    assert set(
        ["workflow_id", "run_id", "task_queue", "capsule_id", "version"]
    ).issubset(data.keys())
    assert data["capsule_id"] == payload["capsule_id"]
    assert data["version"] == payload["version"]

    # The fake temporal client should have a handle stored under the workflow id
    workflow_id = data["workflow_id"]
    assert workflow_id in fake_temporal.workflows


def test_capsule_run_status(api_client):
    client, _ = api_client

    payload = {
        "tenant": "tenant-z",
        "user": "user-q",
        "capsule_id": "org/tool",
        "version": "0.0.1",
        "params": {},
        "metadata": {"run_id": "run-xyz"},
    }

    start = client.post("/v1/capsule/run", json=payload)
    assert start.status_code == status.HTTP_202_ACCEPTED
    workflow_id = start.json()["workflow_id"]

    # Fetch status via the capsule GET endpoint
    status_resp = client.get(f"/v1/capsule/{workflow_id}")
    assert status_resp.status_code == status.HTTP_200_OK
    body = status_resp.json()
    assert body["workflow_id"] == workflow_id
    assert body["status"] in ("completed", "running", "open")
