"""FastAPI application for the SomaGent Constitution service."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager, suppress
from random import uniform
from typing import Iterable

import httpx
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from .api.routes import router
from .core.cache import close_redis_client, create_redis_client
from .core.config import settings
from .core.constitution import (
    ConstitutionRegistry,
    build_verified_from_bundle,
    load_verified_constitution,
)
from .core.models import ConstitutionBundle

logger = logging.getLogger(__name__)

SYNC_TIMESTAMP_GAUGE = Gauge(
    "constitution_sync_timestamp",
    "Unix timestamp of the last successful constitution sync per tenant.",
    labelnames=("tenant",),
)

SYNC_VERSION_GAUGE = Gauge(
    "constitution_hash_version",
    "Tracks the currently active constitution hash per tenant.",
    labelnames=("tenant",),
)

SYNC_ERROR_COUNTER = Counter(
    "constitution_sync_errors_total",
    "Number of failed attempts to refresh the constitution.",
)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        verified = load_verified_constitution(settings.bundle_path, settings.public_key_path)
        redis_client = await create_redis_client(str(settings.redis_url))
        if redis_client is None:
            logger.warning("Redis unavailable; serving constitution from in-memory registry only")
        else:
            for tenant in settings.tenants:
                await redis_client.setex(f"constitution:{tenant}", settings.cache_ttl_seconds, verified.hash)
        registry = ConstitutionRegistry(verified, tenants=settings.tenants)
        app.state.redis_client = redis_client
        app.state.constitution_registry = registry
        for tenant in settings.tenants:
            _record_sync_metrics(tenant, verified.hash)

        stop_event = asyncio.Event()
        tasks: list[asyncio.Task[None]] = []
        if settings.sync_enabled:
            tasks.append(asyncio.create_task(_sync_constitution_loop(app, stop_event, settings.tenants)))
        try:
            yield
        finally:
            stop_event.set()
            for task in tasks:
                task.cancel()
            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task
            await close_redis_client(redis_client)

    app = FastAPI(
        title="SomaGent Constitution Service",
        version="0.2.0",
        description="Serves the signed SomaGent constitution with cryptographic verification.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        registry_present = hasattr(app.state, "constitution_registry")
        status = "ok" if registry_present else "degraded"
        return {"status": status, "service": settings.service_name}

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "SomaGent Constitution Service"}

    app.include_router(router)
    return app


app = create_app()


def _record_sync_metrics(tenant: str, hash_value: str) -> None:
    SYNC_TIMESTAMP_GAUGE.labels(tenant=tenant).set(time.time())
    # Use an integer-friendly representation by hashing hex string to float length if needed.
    try:
        numeric = int(hash_value[:12], 16)
    except ValueError:
        numeric = 0
    SYNC_VERSION_GAUGE.labels(tenant=tenant).set(numeric)


async def _persist_hashes(redis, tenants: Iterable[str], hash_value: str) -> None:
    if redis is None:
        return
    for tenant in tenants:
        await redis.setex(f"constitution:{tenant}", settings.cache_ttl_seconds, hash_value)


async def _pull_remote_bundle(client: httpx.AsyncClient) -> ConstitutionBundle:
    url = settings.somabrain_base_url.rstrip("/") + "/v1/constitution"
    response = await client.get(url, timeout=settings.http_timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    return ConstitutionBundle.model_validate(payload)


async def _sync_constitution_loop(app: FastAPI, stop_event: asyncio.Event, tenants: Iterable[str]) -> None:
    interval = max(5.0, settings.sync_interval_seconds)
    jitter = min(0.2 * interval, 30.0)
    registry: ConstitutionRegistry = app.state.constitution_registry
    redis = getattr(app.state, "redis_client", None)

    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            try:
                bundle = await _pull_remote_bundle(client)
                verified = build_verified_from_bundle(bundle, settings.public_key_path)
                current_hash = registry.bundle.hash
                if verified.hash != current_hash:
                    registry.update(verified)
                    await _persist_hashes(redis, tenants, verified.hash)
                    logger.info(
                        "Updated constitution to version=%s hash=%s",
                        verified.bundle.version,
                        verified.hash,
                    )
                for tenant in tenants:
                    _record_sync_metrics(tenant, verified.hash)
            except httpx.HTTPStatusError as exc:
                SYNC_ERROR_COUNTER.inc()
                logger.warning("SomaBrain returned HTTP error during sync: %s", exc)
            except httpx.HTTPError as exc:
                SYNC_ERROR_COUNTER.inc()
                logger.warning("Failed to contact SomaBrain for constitution sync: %s", exc)
            except Exception as exc:  # pragma: no cover - defensive
                SYNC_ERROR_COUNTER.inc()
                logger.exception("Unexpected error during constitution sync: %s", exc)

            sleep_for = interval + (uniform(-jitter, jitter) if jitter else 0.0)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                continue
