from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager, suppress
from random import uniform
from typing import Any, Dict, Iterable, List

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .observability import setup_observability

from .constitution_cache import get_cached_hash, invalidate_hash
from .core.engine import compute_severity, evaluate as evaluate_engine
from .policy_rules import PolicyRule, bootstrap_rule_engine, get_rules, list_tenants
from .redis_client import get_constitution_hash

try:  # pragma: no cover - optional dependency during local dev
    from aiokafka import AIOKafkaConsumer
except ImportError:  # pragma: no cover
    AIOKafkaConsumer = None


EVALUATION_COUNTER = Counter(
    "policy_evaluations_total",
    "Number of policy evaluations performed",
    labelnames=("tenant", "decision", "severity"),
)

EVALUATION_LATENCY = Histogram(
    "policy_evaluation_latency_seconds",
    "Latency of policy evaluation handler",
    labelnames=("tenant",),
    buckets=(0.001, 0.005, 0.01, 0.015, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

EVALUATION_SCORE = Histogram(
    "policy_evaluation_score",
    "Distribution of policy evaluation scores",
    labelnames=("tenant",),
    buckets=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
)


async def _prefetch_constitution_hashes(stop_event: asyncio.Event, interval_seconds: float = 300.0) -> None:
    """Periodically prefetch constitution hashes to keep the local cache warm."""

    jitter = 0.1 * interval_seconds
    while not stop_event.is_set():
        tenants: Iterable[str] = list_tenants()
        tenant_list = list(tenants) or ["global"]
        for tenant in tenant_list:
            if stop_event.is_set():  # pragma: no branch - cooperative cancel
                break
            try:
                await get_cached_hash(tenant)
            except Exception:
                continue
        sleep_for = max(5.0, interval_seconds + uniform(-jitter, jitter))
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=sleep_for)
        except asyncio.TimeoutError:
            continue


async def _listen_constitution_updates(stop_event: asyncio.Event, max_backoff: float = 30.0) -> None:
    """Consume ``constitution.updated`` events and invalidate cached hashes with backoff."""

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap or AIOKafkaConsumer is None:
        return

    backoff = 1.0
    topics = ["constitution.updated"]

    while not stop_event.is_set():
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap.split(","),
            group_id="policy_engine_cache_invalidator",
            enable_auto_commit=True,
            auto_offset_reset="earliest",
        )
        try:
            await consumer.start()
            backoff = 1.0
            async for msg in consumer:
                if stop_event.is_set():
                    break
                try:
                    data = json.loads(msg.value.decode("utf-8"))
                except Exception:
                    continue
                tenant = data.get("tenant")
                if tenant:
                    try:
                        await invalidate_hash(tenant)
                    except Exception:
                        continue
        except asyncio.CancelledError:  # pragma: no cover - cooperative cancel
            break
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            with suppress(Exception):
                await consumer.stop()
        if stop_event.is_set():
            break


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .core.rule_store import load_and_cache_rules
    from .policy_rules import get_rules
    
    await bootstrap_rule_engine()
    
    # Persist canonical rule packs to Redis for all tenants
    for tenant in list_tenants() or ["global"]:
        rules = get_rules(tenant)
        await load_and_cache_rules(tenant, rules)
    
    stop_event = asyncio.Event()
    tasks = [
        asyncio.create_task(_prefetch_constitution_hashes(stop_event)),
        asyncio.create_task(_listen_constitution_updates(stop_event)),
    ]
    try:
        yield
    finally:
        stop_event.set()
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(lifespan=lifespan)

# REAL OpenTelemetry instrumentation - no mocks, exports to Prometheus
setup_observability("policy-engine", app, service_version="0.1.0")


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
    elapsed = time.perf_counter() - started
    EVALUATION_COUNTER.labels(tenant=req.tenant, decision=decision, severity=severity).inc()
    EVALUATION_LATENCY.labels(tenant=req.tenant).observe(elapsed)
    EVALUATION_SCORE.labels(tenant=req.tenant).observe(score)
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
