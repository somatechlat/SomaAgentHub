from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = PROJECT_ROOT / "services" / "notification-service"
sys.path.insert(0, str(SERVICE_ROOT))

from app.core.bus import get_notification_bus  # type: ignore  # noqa: E402
from app.core.config import settings  # type: ignore  # noqa: E402
from app.main import app  # type: ignore  # noqa: E402

client = TestClient(app)


def setup_function() -> None:
    settings.use_kafka = False
    bus = get_notification_bus(settings)
    bus.cache.clear()


def test_enqueue_notification_returns_record() -> None:
    payload = {
        "tenant_id": "tenant-123",
        "channel": "ops",
        "message": "Capsule throughput degraded",
        "severity": "warning",
        "metadata": {"capsule_id": "capsule-9"},
    }

    response = client.post("/v1/notifications", json=payload)
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    record = body["record"]
    assert record["tenant_id"] == payload["tenant_id"]
    assert record["metadata"]["capsule_id"] == "capsule-9"
    assert record["timestamp"]


def test_backlog_endpoint_filters_by_tenant() -> None:
    first = {
        "tenant_id": "tenant-a",
        "channel": "ops",
        "message": "First message",
    }
    second = {
        "tenant_id": "tenant-b",
        "channel": "ops",
        "message": "Second message",
    }
    assert client.post("/v1/notifications", json=first).status_code == 202
    assert client.post("/v1/notifications", json=second).status_code == 202

    backlog_a = client.get("/v1/notifications/backlog", params={"tenant_id": "tenant-a"})
    assert backlog_a.status_code == 200
    results_a = backlog_a.json()["results"]
    assert len(results_a) == 1
    assert results_a[0]["tenant_id"] == "tenant-a"

    backlog_all = client.get("/v1/notifications/backlog", params={"limit": 1})
    assert backlog_all.status_code == 200
    results_all = backlog_all.json()["results"]
    assert len(results_all) == 1