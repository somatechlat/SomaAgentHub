# Simple async Redis client for the Policy Engine
# Uses redis.asyncio; falls back to a no‑op stub if the library is missing.

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None


async def get_constitution_hash(tenant: str) -> str:
    """Return a cached constitution hash for *tenant*.

    In a real deployment this reads ``constitution:{tenant}`` from Redis.
    If Redis is unavailable we return a deterministic placeholder.
    """
    # If the redis library is missing or the connection URL is not provided, use a stub.
    if redis is None:
        return f"constitution-hash-{tenant}"

    # Allow tests to run without a live Redis instance by checking env var.
    import os

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        # No URL -> fallback to deterministic placeholder.
        return f"constitution-hash-{tenant}"

    client = redis.from_url(redis_url)
    key = f"constitution:{tenant}"
    try:
        val = await client.get(key)
    except Exception:  # pragma: no cover
        # Any connection error falls back to placeholder.
        await client.close()
        return f"constitution-hash-{tenant}"
    await client.close()
    if val is None:
        # placeholder when not set
        return f"constitution-hash-{tenant}"
    return val.decode()
