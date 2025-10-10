"""Redis client helpers for the gateway using the shared RedisClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from services.common.redis_client import RedisClient


def get_redis_client() -> RedisClient:
    """Return the shared RedisClient instance configured via Settings."""

    from services.common.redis_client import get_redis_client as _get_redis_client

    from ..config import get_sah_settings

    settings = get_sah_settings()
    if settings.redis.url:
        # The common Redis client reads REDIS_URL; set it once before first use.
        # This avoids per-call environment mutation while keeping compatibility.
        import os

        os.environ.setdefault("REDIS_URL", settings.redis.url)
    return _get_redis_client()


async def close_redis_client() -> None:
    """Close the shared Redis connection when the service shuts down."""

    from services.common.redis_client import get_redis_client as _get_redis_client

    client = _get_redis_client()
    await client.close()
