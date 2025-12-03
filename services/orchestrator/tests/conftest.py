import pytest
from fastapi.testclient import TestClient

from services.orchestrator.app.main import build_app


@pytest.fixture
def api_client():
    app = build_app()
    client = TestClient(app)
    return client, app
