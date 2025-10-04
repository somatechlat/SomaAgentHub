from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .constitution_cache import invalidate_hash
from .core.engine import compute_severity, evaluate as evaluate_engine
from .policy_rules import PolicyRule, get_rules
from .redis_client import get_constitution_hash

try:  # pragma: no cover - optional dependency during local dev
    from aiokafka import AIOKafkaConsumer
except ImportError:  # pragma: no cover
    AIOKafkaConsumer = None

app = FastAPI()


class EvalRequest(BaseModel):
    session_id: str
    tenant: str
    user: str
    prompt: str
    role: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvalResponse(BaseModel):
    allowed: bool
    score: float
    severity: str
    reasons: Dict[str, Any]


EVALUATION_COUNTER = Counter(
    "policy_evaluations_total",
    "Number of policy evaluations performed",
    labelnames=("tenant", "decision"),
)

EVALUATION_LATENCY = Histogram(
    "policy_evaluation_latency_seconds",
    "Latency of policy evaluation handler",
)


def _rule_to_dict(rule: PolicyRule) -> Dict[str, Any]:
    return {
        "name": rule.name,
        "pattern": rule.pattern,
        "weight": rule.weight,
        "description": rule.description,
        "severity": rule.severity,
    }


@app.post("/v1/evaluate", response_model=EvalResponse)
async def evaluate(req: EvalRequest):
    started = time.perf_counter()
    allowed, score, violations, constitution_hash = await evaluate_engine(req.tenant, req.prompt)
    severity = compute_severity(score)
    reasons: Dict[str, Any] = {
        "constitution_hash": constitution_hash,
        "policy": violations,
    }
    decision = "allow" if allowed else "deny"
    EVALUATION_COUNTER.labels(tenant=req.tenant, decision=decision).inc()
    EVALUATION_LATENCY.observe(time.perf_counter() - started)
    return EvalResponse(allowed=allowed, score=score, severity=severity, reasons=reasons)


@app.get("/health", tags=["system"])
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "policy-engine"}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "SomaGent Policy Engine"}


# Compatibility wrapper for legacy scripts that expect a sync function
def evaluate_sync(req: EvalRequest):
    return asyncio.run(evaluate(req))


@app.get("/v1/policies/{tenant}", response_model=List[Dict[str, Any]])
def list_policies(tenant: str) -> List[Dict[str, Any]]:
    """Return the list of forbidden substrings for *tenant*.

    This endpoint is useful for debugging and for the UI to display the
    active policy rules.
    """
    return [_rule_to_dict(rule) for rule in get_rules(tenant)]


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
    if not bootstrap or AIOKafkaConsumer is None:
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
                # Log silently – in a system we'd emit a metric.
                continue
    finally:
        await consumer.stop()


@app.on_event("startup")
async def _startup_background_tasks() -> None:
    # Fire‑and‑forget the update listener – it runs for the lifetime of the app.
    asyncio.create_task(_listen_constitution_updates())
