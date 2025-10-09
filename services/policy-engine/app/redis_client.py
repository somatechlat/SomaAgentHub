"""Async Redis access convenience for the Policy Engine.

Exports:
- redis_client: an async Redis client or None if unavailable/misconfigured.
- get_constitution_hash: helper to fetch constitution hash with safe fallbacks.
"""

from __future__ import annotations

import os
from typing import Optional

try:  # pragma: no cover
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore


def _build_client() -> Optional["redis.Redis"]:
    if redis is None:
        return None
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        return redis.from_url(url)
    except Exception:  # pragma: no cover
        return None


# Exported client used by store modules
redis_client = _build_client()


async def get_constitution_hash(tenant: str) -> str:
    """Return a cached constitution hash for tenant with safe fallback."""
    client = redis_client
    if client is None:
        return f"constitution-hash-{tenant}"
    key = f"constitution:{tenant}"
    try:
        val = await client.get(key)
    except Exception:  # pragma: no cover
        return f"constitution-hash-{tenant}"
    if val is None:
        return f"constitution-hash-{tenant}"
    try:
        return val.decode()
    except Exception:
        return f"constitution-hash-{tenant}"
