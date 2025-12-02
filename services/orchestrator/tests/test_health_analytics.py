from fastapi import status


def test_root_health(api_client):
    client, _ = api_client
    resp = client.get("/health")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "ok"


def test_metrics_endpoint(api_client):
    client, _ = api_client
    resp = client.get("/metrics")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers["content-type"].startswith("text/plain")
    assert b"# HELP" in resp.content
