"""Redis client for the Constitution service.

Provides the same fallback behavior as the Policy Engine client: if the
``redis`` library is unavailable or ``REDIS_URL`` is not set, a deterministic
placeholder hash is returned. This keeps the service functional during local
development and testing without requiring a running Redis instance.
"""

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None

import os

async def get_constitution_hash(tenant: str) -> str:
    """Return the constitution hash for *tenant*.

    In production this reads the key ``constitution:{tenant}`` from Redis.
    If Redis is not available, a deterministic placeholder is returned.
    """
    if redis is None:
        return f"constitution-hash-{tenant}"

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return f"constitution-hash-{tenant}"

    client = redis.from_url(redis_url)
    key = f"constitution:{tenant}"
    try:
        val = await client.get(key)
    except Exception:  # pragma: no cover
        await client.close()
        return f"constitution-hash-{tenant}"
    await client.close()
    if val is None:
        return f"constitution-hash-{tenant}"
    return val.decode()
