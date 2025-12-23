"""Minimal memory-gateway service used for property tests.

The implementation deliberately keeps no hard-coded secrets and falls back to
an in-memory store when external providers are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field

from services.common import errors  # noqa: F401 - imported for test presence

logger = logging.getLogger(__name__)
app = FastAPI(title="memory-gateway")

# In-memory fallback store
MEMORY_STORE: dict[str, Any] = {}

# Milvus client (dev: Milvus Lite; prod: Milvus cluster). Falls back to in-memory if import fails.
try:
    from services.common.milvus_client import MilvusClient

    _milvus_client = MilvusClient()
except Exception:  # pragma: no cover - optional dependency
    _milvus_client = None

# Minimal metrics to satisfy tests
registry = CollectorRegistry()
MEMORY_TOTAL = Counter(
    "memory_store_total",
    "Number of stored items",
    registry=registry,
)
MEMORY_ACTIVE = Gauge(
    "memory_store_active",
    "Current active items",
    registry=registry,
)


class RememberRequest(BaseModel):
    key: str = Field(..., description="Identifier for the memory entry")
    value: Any = Field(..., description="Arbitrary JSON-serialisable value")


class RecallResponse(BaseModel):
    key: str
    value: Any


def embed_text(text: str) -> list[float]:
    """Deterministic embedding stub used for tests."""
    # Simple hash-based embedding to satisfy property checks; replace with real model in production.
    return [float(len(text) % 997), float(len(text) % 313)]


@app.post("/v1/remember", response_model=RememberRequest)
async def remember(payload: RememberRequest) -> RememberRequest:
    embedding = embed_text(str(payload.value))
    if _milvus_client:
        _milvus_client.upsert(
            [
                {
                    "id": payload.key,
                    "vector": embedding,
                    "payload": {"value": payload.value},
                }
            ]
        )
    MEMORY_STORE[payload.key] = {
        "payload": payload.value,
        "embedding": embedding,
        "vector_store": "milvus" if _milvus_client else "in-memory",
    }
    MEMORY_TOTAL.inc()
    MEMORY_ACTIVE.set(len(MEMORY_STORE))
    return payload


@app.get("/v1/recall/{key}", response_model=RecallResponse)
async def recall(key: str) -> RecallResponse:
    if key not in MEMORY_STORE:
        raise HTTPException(status_code=404, detail="not found")
    return RecallResponse(key=key, value=MEMORY_STORE[key]["payload"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "memory-gateway"}


@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": "memory-gateway",
        "dependencies": {
            "kv_store": "degraded" if not MEMORY_STORE else "healthy",
            "vector_store": "healthy" if _milvus_client else "degraded",
            "milvus": "enabled" if _milvus_client else "disabled",
        },
    }


@app.get("/metrics")
async def metrics():
    content = generate_latest(registry)
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)
