"""Redis client helpers for the gateway."""

from __future__ import annotations

from typing import Optional

import redis.asyncio as redis

from .config import get_settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Return a cached Redis client instance."""

    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    """Close the Redis connection when the service shuts down."""

    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
