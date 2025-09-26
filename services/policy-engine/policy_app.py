from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, List
from .policy_rules import get_rules
import asyncio
import os
from .constitution_cache import get_cached_hash, invalidate_hash
from .redis_client import get_constitution_hash
from aiokafka import AIOKafkaConsumer

app = FastAPI()


class EvalRequest(BaseModel):
    session_id: str
    tenant: str
    user: str
    prompt: str
    role: str
    metadata: Dict[str, Any] = {}


class EvalResponse(BaseModel):
    allowed: bool
    score: float
    reasons: Dict[str, str]


@app.post("/v1/evaluate", response_model=EvalResponse)
async def evaluate(req: EvalRequest):
    # Debug: print incoming request
    print("[DEBUG] evaluate called with:", req.dict())
    # consult constitution hash via TTL cache (fallback to Redis if needed)
    ch = await get_cached_hash(req.tenant)
    # Apply rule engine: deny if any forbidden substring defined for the tenant appears in the prompt.
    forbidden_terms = get_rules(req.tenant)
    lowered = req.prompt.lower()
    for term in forbidden_terms:
        if term.lower() in lowered:
            result = EvalResponse(
                allowed=False,
                score=0.0,
                reasons={"policy": f"contains forbidden term '{term}'", "constitution_hash": ch},
            )
            # Debug: print result before returning
            print("[DEBUG] evaluate result:", result.dict())
            return result
    # If no rule blocks the request, allow it with a default score.
    result = EvalResponse(allowed=True, score=0.9, reasons={"constitution_hash": ch})
    print("[DEBUG] evaluate result:", result.dict())
    return result


# Compatibility wrapper for legacy scripts that expect a sync function
def evaluate_sync(req: EvalRequest):
    import asyncio

    return asyncio.run(evaluate(req))


@app.get("/v1/policies/{tenant}", response_model=List[str])
def list_policies(tenant: str) -> List[str]:
    """Return the list of forbidden substrings for *tenant*.

    This endpoint is useful for debugging and for the UI to display the
    active policy rules.
    """
    return get_rules(tenant)


@app.get("/v1/health/redis")
async def health_redis() -> dict:
    """Async health check that pings Redis (or fallback) and reports status.

    Returns ``{"status": "ok"}`` with HTTP 200 when the Redis client can be reached
    (or when the fallback placeholder is used). Returns ``{"status": "unavailable"}``
    with HTTP 503 otherwise.
    """
    try:
        # Await the async Redis client call – it returns a placeholder quickly if Redis is unavailable.
        _ = await get_constitution_hash("health-check")
        return {"status": "ok"}
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable")


# ---------------------------------------------------------------------------
# Background task: listen for constitution updates and invalidate the cache.
# ---------------------------------------------------------------------------
async def _listen_constitution_updates() -> None:
    """Consume ``constitution.updated`` events and invalidate cached hashes.

    The event payload is expected to be a JSON object with a ``tenant`` field.
    If the Kafka broker is not configured, the listener is silently disabled –
    this keeps local development simple.
    """
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap:
        # No broker – nothing to listen to.
        return
    consumer = AIOKafkaConsumer(
        "constitution.updated",
        bootstrap_servers=bootstrap.split(","),
        group_id="policy_engine_cache_invalidator",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                import json

                data = json.loads(msg.value.decode("utf-8"))
                tenant = data.get("tenant")
                if tenant:
                    await invalidate_hash(tenant)
            except Exception:
                # Log silently – in a real system we'd emit a metric.
                continue
    finally:
        await consumer.stop()


@app.on_event("startup")
async def _startup_background_tasks() -> None:
    # Fire‑and‑forget the update listener – it runs for the lifetime of the app.
    asyncio.create_task(_listen_constitution_updates())
