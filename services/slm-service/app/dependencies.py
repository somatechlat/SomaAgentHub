"""Dependencies for the SLM service."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from .core.config import Settings, get_settings
from .core.providers import SyncProvider, get_provider


@lru_cache
def get_default_provider(settings: Settings | None = None) -> SyncProvider:
    settings = settings or get_settings()
    return get_provider(settings.default_provider)


def provider_dependency(settings: Settings = Depends(get_settings)) -> SyncProvider:
    return get_provider(settings.default_provider)


async def get_redis(settings: Settings = Depends(get_settings)):
    import redis.asyncio as redis

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def queue_manager_dependency(redis_client=Depends(get_redis), settings: Settings = Depends(get_settings)):
    from .core.queue import QueueManager

    return QueueManager(redis_client, settings)


def queue_worker_dependency(redis_client=Depends(get_redis), settings: Settings = Depends(get_settings)):
    from .core.queue import QueueWorker

    def provider_lookup(name: str) -> SyncProvider:
        return get_provider(name)

    return QueueWorker(redis_client, provider_lookup, settings)
