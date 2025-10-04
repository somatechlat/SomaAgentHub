"""Integration test scaffold for the full request flow.

The test demonstrates the intended steps without requiring the full Docker‑Compose stack.
It uses FastAPI TestClient for the Identity and Gateway services, and mocks the
Kafka producer/consumer and Redis client used by the Policy Engine.
Replace the mocks with real testcontainers when you need a true end‑to‑end run.
"""

import asyncio
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytest.importorskip("testcontainers.redis")
pytest.importorskip("testcontainers.kafka")

from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

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
    os.environ["REDIS_URL"] = container.get_connection_url()
    yield container
    container.stop()

@pytest.fixture(scope="session")
def kafka_container():
    """Start a real Kafka container for the duration of the test session."""
    container = KafkaContainer(image="bitnami/kafka:3.5")
    container.start()
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = container.get_bootstrap_server()
    yield container
    container.stop()

@pytest.fixture(scope="session", autouse=True)
def start_slm_worker(kafka_container, redis_container):
    """Run the real SLM async worker using the real Kafka broker."""
    from slm.worker import start_worker
    loop = asyncio.get_event_loop()
    task = loop.create_task(start_worker())
    yield
    task.cancel()
    try:
        loop.run_until_complete(task)
    except Exception:
        pass

def test_end_to_end_flow(identity_client, gateway_client, policy_client):
    # 1. Obtain JWT from identity service.
    user_id = "user123"
    tenant_id = "tenantA"
    token = get_jwt_token(identity_client, user_id, tenant_id)

    # 2. Call gateway to start a session (this forwards to orchestrator – we mock it).
    # For the purpose of this scaffold we bypass the orchestrator call by mocking httpx.
    session_payload = {
        "prompt": "hello world",
        "capsule_id": None,
        "metadata": {},
    }
    headers = {"Authorization": f"Bearer {token}"}

    # Spin up a minimal orchestrator FastAPI app that returns a session.
    orchestrator_app = FastAPI()

    @orchestrator_app.post("/v1/sessions/start")
    async def start_session(payload: dict):
        return {"session_id": "sess-1", "status": "accepted"}

    orchestrator_client = TestClient(orchestrator_app)
    # Point the gateway to this orchestrator.
    os.environ["SOMAGENT_GATEWAY_ORCHESTRATOR_URL"] = orchestrator_client.base_url
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

    # 4. Send an SLM request using the producer (mocked) and verify a response.
    from services.slm_service.slm.producer import Producer
    prod = Producer()
    # Send a real request to Kafka; the background worker will process it.
    asyncio.run(prod.send(session_id, "assistant", "test prompt", {}))

    # Consume the response from the real Kafka topic to verify.
    from aiokafka import AIOKafkaConsumer
    consumer = AIOKafkaConsumer(
        "slm.responses",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS").split(","),
        group_id="test_consumer",
        auto_offset_reset="earliest",
    )
    async def _consume_one():
        await consumer.start()
        try:
            async for msg in consumer:
                return msg.value
        finally:
            await consumer.stop()
    response_bytes = asyncio.run(_consume_one())
    assert response_bytes is not None
    import json
    resp_obj = json.loads(response_bytes)
    assert resp_obj["session_id"] == session_id

    # 5. Verify the policy engine health‑check works.
    health = policy_client.get("/v1/health/redis")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"