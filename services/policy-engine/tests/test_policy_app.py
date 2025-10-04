import os
import asyncio
from fastapi.testclient import TestClient

# Ensure Redis fallback (no REDIS_URL) for deterministic behavior
if "REDIS_URL" in os.environ:
    del os.environ["REDIS_URL"]

from app.policy_app import app, EvalRequest, evaluate_sync
from app.constitution_cache import get_cached_hash, invalidate_hash

client = TestClient(app)

def test_evaluate_allowed():
    payload = {
        "session_id": "s1",
        "tenant": "tenantA",
        "user": "user1",
        "prompt": "hello world",
        "role": "assistant",
        "metadata": {}
    }
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["severity"] == "low"
    assert "constitution_hash" in data["reasons"]
    assert data["reasons"]["policy"] == []

def test_evaluate_forbidden():
    payload = {
        "session_id": "s2",
        "tenant": "tenantA",  # tenantA has "forbidden" rule
        "user": "user2",
        "prompt": "this is forbidden content",
        "role": "assistant",
        "metadata": {},
    }
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is False
    assert data["severity"] in {"medium", "high", "critical"}
    assert data["reasons"]["policy"]
    first_violation = data["reasons"]["policy"][0]
    assert first_violation["pattern"] == "forbidden"

def test_evaluate_sync_wrapper():
    req = EvalRequest(
        session_id="s3",
        tenant="tenantC",
        user="user3",
        prompt="sync test",
        role="assistant",
        metadata={}
    )
    result = evaluate_sync(req)
    # evaluate_sync runs the async endpoint via asyncio.run, returning the Pydantic model
    assert result.allowed is True
    assert isinstance(result.reasons, dict)
    assert result.reasons["policy"] == []

def test_evaluate_forbidden_term():
    payload = {
        "session_id": "sess1",
        "tenant": "tenantA",
        "user": "user1",
        "prompt": "This contains a forbidden word",
        "role": "test",
        "metadata": {},
    }
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is False
    patterns = [v["pattern"] for v in data["reasons"]["policy"]]
    assert "forbidden" in patterns

def test_list_policies():
    response = client.get("/v1/policies/tenantA")
    assert response.status_code == 200
    policies = response.json()
    assert isinstance(policies, list)
    patterns = [policy["pattern"] for policy in policies]
    assert "forbidden" in patterns
    assert "blocked" in patterns

# Simple cache test – call get_cached_hash twice and ensure same result (placeholder)
async def _run_cache_test():
    hash1 = await get_cached_hash("tenantA")
    hash2 = await get_cached_hash("tenantA")
    assert hash1 == hash2
    await invalidate_hash("tenantA")
    hash3 = await get_cached_hash("tenantA")
    # After invalidation, value may be same placeholder but ensure function runs without error
    assert isinstance(hash3, str)

def test_constitution_cache_behavior():
    asyncio.run(_run_cache_test())
