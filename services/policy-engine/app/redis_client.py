"""Async Redis access for the Policy Engine using the shared Redis client.

Exports:
- redis_client: an async Redis client or None if unavailable/misconfigured.
- get_constitution_hash: helper to fetch constitution hash with safe fallbacks.
"""

from __future__ import annotations

import os

try:  # pragma: no cover
    from services.common.redis_client import get_redis_client
except Exception:  # pragma: no cover
    get_redis_client = None  # type: ignore


async def _build_client():
    if get_redis_client is None:
        return None
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        client_wrap = get_redis_client()
        return await client_wrap.get_client()
    except Exception:  # pragma: no cover
        return None


# Exported client used by store modules
# Note: policy modules can await _ensure_client() to lazily establish connection
redis_client = None

async def _ensure_client():
    global redis_client
    if redis_client is None:
        redis_client = await _build_client()
    return redis_client


async def get_constitution_hash(tenant: str) -> str:
    """Return a cached constitution hash for tenant with safe fallback."""
    client = await _ensure_client()
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
