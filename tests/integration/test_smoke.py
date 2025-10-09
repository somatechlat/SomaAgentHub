import os
import pytest
import requests


RUN = os.getenv("RUN_INTEGRATION", "0")


@pytest.mark.skipif(RUN != "1", reason="Integration tests are disabled by default")
def test_gateway_orchestrator_smoke():
    # This test expects the dev infra to be running and services available at the example ports
    gw = os.getenv("GATEWAY_URL", "http://localhost:60010")
    token = os.getenv("DEV_JWT_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = {"prompt": "Test", "capsule_id": "dev", "metadata": {}}
    resp = requests.post(f"{gw}/v1/sessions", json=data, headers=headers, timeout=10)
    assert resp.status_code in (200, 201, 202)
