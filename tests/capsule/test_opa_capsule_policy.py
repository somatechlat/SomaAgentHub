import pytest

from services.common.opa_client import OPAClient
from services.common.config.base_settings import resolve_env


class DummyTransport:
    async def handle_async_request(self, request):
        # Very small mock that returns allowed when role present
        from httpx import Response

        return Response(200, json={"result": {"allowed": True}})


class DummyClient:
    def __init__(self, *a, **kw):
        self._closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def send(self, request):
        from httpx import Response

        return Response(200, json={"result": {"allowed": True}})


@pytest.mark.asyncio
async def test_allow_write_capsule_results_allows_when_policy_true(monkeypatch):
    import services.common.opa_client as mod

    def patched_factory(*a, **kw):
        return DummyClient()

    monkeypatch.setattr(mod.httpx, "AsyncClient", patched_factory)

    client = OPAClient(opa_url="http://opa:8181")
    allowed = await client.allow_write_capsule_results(
        user="tenant-owner",
        tenant="tenant",
        capsule="demo",
        version="1.0.0",
        roles=["capsule.writer"],
    )
    assert allowed is True
