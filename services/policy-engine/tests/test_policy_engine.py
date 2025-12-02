"""
Tests for the minimal Policy Engine service.

The policy engine implements a very small rule set based on the ``ALLOWED_ACTIONS``
environment variable. The tests spin up a FastAPI ``TestClient`` and verify:

1. The health endpoint returns ``200 OK`` with body ``OK``.
2. The ``/v1/allow`` endpoint correctly allows or denies based on the
configured actions.
3. The metrics endpoint is reachable and increments the request counter.
"""

import os

from fastapi.testclient import TestClient

# Import the FastAPI app from the service implementation
from app.main import app  # type: ignore

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == "OK"


def test_allow_endpoint_denied_by_default():
    # Ensure no allowed actions are set for this test
    os.environ.pop("ALLOWED_ACTIONS", None)
    response = client.post(
        "/v1/allow",
        json={"subject": "user1", "action": "read", "resource": "memory"},
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": False}


def test_allow_endpoint_allowed_when_configured():
    os.environ["ALLOWED_ACTIONS"] = "read:memory,write:memory"
    # Re-import to pick up the new env var (the module caches config at import time)
    # Force a reload of the module to apply the env var changes.
    import importlib

    import app.main as policy_mod  # type: ignore

    importlib.reload(policy_mod)
    test_client = TestClient(policy_mod.app)

    response = test_client.post(
        "/v1/allow",
        json={"subject": "user2", "action": "read", "resource": "memory"},
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": True}


def test_metrics_endpoint():
    # Call the allow endpoint once to increment the counter
    client.post(
        "/v1/allow",
        json={"subject": "u", "action": "x", "resource": "y"},
    )
    response = client.get("/metrics")
    assert response.status_code == 200
    # The metric name should be present in the output
    assert "policy_engine_requests_total" in response.text
