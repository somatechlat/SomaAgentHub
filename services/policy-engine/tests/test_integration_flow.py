"""Integration test for the full request flow using REAL services (no mocks)."""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("testcontainers.redis")
pytest.importorskip("testcontainers.kafka")

from testcontainers.kafka import KafkaContainer
from testcontainers.redis import RedisContainer
from services.common.config.base_settings import resolve_env


# Fixtures will import the service apps after environment variables are set.
@pytest.fixture
def identity_app():
    from services.identity_service.app.main import app

    return app


@pytest.fixture
def gateway_app():
    # Ensure orchestrator URL is set before importing the gateway.
    from services.gateway_api.app.main import app

    return app


@pytest.fixture
def policy_app():
    from services.policy_engine.policy_app import app

    return app


# Helper to issue a JWT from the identity service.
def get_jwt_token(client: TestClient, user_id: str, tenant_id: str) -> str:
    # Create a user first
    user_payload = {
        "user_id": user_id,
        "active": True,
        "capabilities": ["default"],
        "mfa_enabled": True,
    }
    client.put(f"/v1/users/{user_id}", json=user_payload)
    # Issue token
    token_req = {"user_id": user_id, "tenant_id": tenant_id, "mfa_code": "dummy"}
    resp = client.post("/v1/tokens/issue", json=token_req)
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def identity_client(identity_app):
    return TestClient(identity_app)


@pytest.fixture
def gateway_client(gateway_app):
    return TestClient(gateway_app)


@pytest.fixture
def policy_client(policy_app):
    return TestClient(policy_app)


@pytest.fixture(scope="session")
def redis_container():
    """Start a real Redis container for the duration of the test session."""
    container = RedisContainer(image="redis:7-alpine")
    container.start()
    # Use the canonical prefix for Redis URL in tests
    os.environ["SOMA_AGENT_HUB_REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def kafka_container():
    """Start a real Kafka container for the duration of the test session."""
    container = KafkaContainer(image="bitnami/kafka:3.5")
    container.start()
    # Use the canonical prefix for Kafka bootstrap servers in tests
    os.environ["SOMA_AGENT_HUB_KAFKA_BOOTSTRAP_SERVERS"] = (
        container.get_bootstrap_server()
    )
    yield container
    container.stop()


@pytest.fixture(scope="session", autouse=True)
def start_llm_hub_stub(kafka_container, redis_container):
    """LLM Hub requires no dedicated background worker for this test structure."""
    yield


def test_end_to_end_flow(identity_client, gateway_client, policy_client):
    # 1. Obtain JWT from identity service.
    user_id = "user123"
    tenant_id = "tenantA"
    token = get_jwt_token(identity_client, user_id, tenant_id)

    # 2. Call gateway to start a session (this forwards to the REAL orchestrator).
    session_payload = {
        "prompt": "hello world",
        "capsule_id": None,
        "metadata": {},
    }
    headers = {"Authorization": f"Bearer {token}"}
    # Ensure gateway is pointed at a real orchestrator via env var
    # Ensure the orchestrator URL is provided via the canonical env prefix.
    # resolve_env expects the unprefixed name; it applies SOMA_AGENT_HUB_
    assert resolve_env(
        "GATEWAY_ORCHESTRATOR_URL"
    ), "Set SOMA_AGENT_HUB_GATEWAY_ORCHESTRATOR_URL to real Orchestrator URL"
    resp = gateway_client.post("/v1/sessions", json=session_payload, headers=headers)
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    # 3. Directly call the Policy Engine evaluate endpoint using the same tenant.
    eval_payload = {
        "session_id": session_id,
        "tenant": tenant_id,
        "user": user_id,
        "prompt": "test prompt",
        "role": "assistant",
        "metadata": {},
    }
    eval_resp = policy_client.post("/v1/evaluate", json=eval_payload)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["allowed"] is True

    # 4. Hub integration tested elsewhere.

    # 5. Verify the policy engine health‑check works.
    health = policy_client.get("/v1/health/redis")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
