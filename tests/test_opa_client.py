"""Tests for the OPA client implementation.

These tests use ``httpx.MockTransport`` to simulate the OPA HTTP API without
requiring a running OPA server. They verify that:

* ``evaluate_policy`` correctly parses the OPA response.
* ``check_authorization`` returns ``True`` when the policy allows the action.
* ``health_check`` reports the server health based on the HTTP status.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from services.common.opa_client import OPAClient


def make_mock_response(json_data: dict[str, Any], status_code: int = 200) -> httpx.Response:
    """Utility to create an ``httpx.Response`` with JSON payload.

    ``httpx.MockTransport`` expects a ``Response`` object that can be returned
    from the request handler.
    """
    return httpx.Response(status_code=status_code, json=json_data)


def test_evaluate_policy_success(monkeypatch):
    """When OPA returns a boolean ``result`` the client should return ``allowed``."""

    # Mock transport that returns ``{"result": true}``
    def handler(request: httpx.Request):
        assert request.method == "POST"
        return make_mock_response({"result": True})

    transport = httpx.MockTransport(handler)
    client = OPAClient(opa_url="http://mock-opa:8181")
    # Patch the internal ``httpx.AsyncClient`` to use our mock transport
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: httpx.AsyncClient(transport=transport))

    result = pytest.run(asyncio=True)(client.evaluate_policy)(
        policy_path="somagent/authorization",
        input_data={"user_id": "admin"},
    )
    assert result == {"allowed": True}


def test_check_authorization_admin_allowed(monkeypatch):
    """The simple admin‑only policy should allow the ``admin`` user."""

    def handler(request: httpx.Request):
        # The request payload contains the ``input`` dict; we verify the user_id.
        payload = request.json()
        assert payload["input"]["user_id"] == "admin"
        return make_mock_response({"result": {"allowed": True}})

    transport = httpx.MockTransport(handler)
    client = OPAClient(opa_url="http://mock-opa:8181")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: httpx.AsyncClient(transport=transport))

    authorized = pytest.run(asyncio=True)(client.check_authorization)(
        tenant_id="demo",
        user_id="admin",
        action="access",
        resource="/test",
        context={},
    )
    assert authorized is True


def test_health_check(monkeypatch):
    """Health check returns ``True`` on HTTP 200 and ``False`` otherwise."""
    # Successful health response
    transport_ok = httpx.MockTransport(lambda _: make_mock_response({}, status_code=200))
    client_ok = OPAClient(opa_url="http://mock-opa:8181")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **kw: httpx.AsyncClient(transport=transport_ok))
    assert pytest.run(asyncio=True)(client_ok.health_check)() is True

    # Failed health response
    transport_fail = httpx.MockTransport(lambda _: make_mock_response({}, status_code=500))
    client_fail = OPAClient(opa_url="http://mock-opa:8181")
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: httpx.AsyncClient(transport=transport_fail),
    )
    assert pytest.run(asyncio=True)(client_fail.health_check)() is False
