"""Tests for the legacy ``/v1/evaluate`` endpoint of the Policy Engine.

The orchestrator historically calls ``/v1/evaluate``; we provide an alias to the
``/v1/allow`` implementation. These tests verify that the alias behaves
identically and respects the ``ALLOWED_ACTIONS`` environment variable.
"""

import os

from fastapi.testclient import TestClient

# Import the FastAPI app from the service implementation
from app.main import app  # type: ignore

client = TestClient(app)


def test_evaluate_endpoint_denied_by_default():
    os.environ.pop("ALLOWED_ACTIONS", None)
    response = client.post(
        "/v1/evaluate",
        json={"subject": "user", "action": "read", "resource": "memory"},
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": False}

    def test_evaluate_endpoint_allowed_when_configured():
        os.environ["ALLOWED_ACTIONS"] = "read:memory,write:memory"
        # Reload the module to pick up the new env var (the service reads it at import)
        import importlib

        import app.main as policy_mod  # type: ignore

        importlib.reload(policy_mod)
        test_client = TestClient(policy_mod.app)

        response = test_client.post(
            "/v1/evaluate",
            json={"subject": "user", "action": "write", "resource": "memory"},
        )

    assert response.status_code == 200
    assert response.json() == {"allowed": True}
