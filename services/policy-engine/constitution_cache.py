from datetime import datetime, timedelta
from typing import Dict, Tuple

from .redis_client import get_constitution_hash as _redis_get_hash

# TTL for cached constitution hashes (seconds)
_CACHE_TTL = 60

# In‑memory cache: tenant -> (hash, expiry datetime)
_cache: Dict[str, Tuple[str, datetime]] = {}

async def get_cached_hash(tenant: str) -> str:
    """Return a cached constitution hash for *tenant*.

    If a cached entry exists and is still fresh (within ``_CACHE_TTL``), return it.
    Otherwise fetch the hash from Redis via ``redis_client.get_constitution_hash`` and
    store it in the in‑memory cache.
    """
    now = datetime.utcnow()
    entry = _cache.get(tenant)
    if entry:
        value, expiry = entry
        if now < expiry:
            return value
    # Cache miss or expired – fetch from Redis (or placeholder) and cache.
    value = await _redis_get_hash(tenant)
    _cache[tenant] = (value, now + timedelta(seconds=_CACHE_TTL))
    return value

async def invalidate_hash(tenant: str) -> None:
    """Invalidate the cached constitution hash for *tenant*.

    Used by the Kafka listener when a ``constitution.updated`` event is received.
    """
    _cache.pop(tenant, None)
