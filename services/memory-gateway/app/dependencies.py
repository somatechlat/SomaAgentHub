"""Shared dependencies for the memory gateway."""

from functools import lru_cache
from typing import AsyncIterator

import redis.asyncio as redis
from fastapi import Depends

from somagent_somabrain import SomaBrainClient

from .core.config import Settings, get_settings


@lru_cache
def get_somabrain_client(settings: Settings | None = None) -> SomaBrainClient:
    """Return a configured SomaBrain client."""

    settings = settings or get_settings()
    return SomaBrainClient(
        base_url=settings.somabrain_url,
        tenant_header=settings.tenant_header,
        timeout_seconds=settings.http_timeout_seconds,
    )


async def get_redis(settings: Settings = Depends(get_settings)) -> AsyncIterator[redis.Redis]:
    """Provide a Redis connection for buffering/sync."""

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
