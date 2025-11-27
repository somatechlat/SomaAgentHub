"""Shared Redis client for SomaGent platform.

Provides connection pooling, async operations, and common patterns
for Redis usage across services (caching, locks, pub/sub).
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from typing import Any

# The Redis client is optional for environments where Redis is not installed.
# We attempt to import the async Redis library. If it is unavailable we raise a
# clear error when the client is instantiated, rather than silently providing a
# stub that masks configuration problems.
try:
	import redis.asyncio as redis  # type: ignore
	from redis.asyncio import Redis  # noqa: F401
	from redis.exceptions import RedisError  # noqa: F401
except Exception as exc:  # pragma: no cover
	# Defer the import error until runtime when a RedisClient is created.
	redis = None
	Redis = None  # type: ignore
	RedisError = Exception


class RedisClient:
	"""Async Redis client with connection pooling.

	The client lazily creates a ``redis.asyncio.Redis`` instance backed by a
	connection pool.  All public methods are async and raise ``RuntimeError``
	with a clear message if the underlying ``redis`` library is missing.
	"""

	def __init__(
		self,
		url: str,
		max_connections: int = 50,
		decode_responses: bool = True,
	) -> None:
		"""Initialize Redis client.

		Args:
			url: Redis connection URL (e.g., ``redis://localhost:6379/0``)
			max_connections: Maximum connections in the pool.
			decode_responses: Auto‑decode bytes to strings.
		"""
		if redis is None:
			raise RuntimeError(
				"redis library not installed. Run: pip install redis[asyncio]"
			)

		self.url = url
		self._pool = redis.ConnectionPool.from_url(
			url,
			max_connections=max_connections,
			decode_responses=decode_responses,
		)
		self._client: Redis | None = None

async def get_client(self) -> Redis:
"""Get or create Redis client."""
if self._client is None:
self._client = redis.Redis(connection_pool=self._pool)
return self._client

async def close(self) -> None:
"""Close Redis connection pool."""
if self._client is not None:
await self._client.close()
self._client = None
if self._pool:
# ConnectionPool.disconnect is sync in redis-py
self._pool.disconnect()

# ============================================================================
# Key-Value Operations
# ============================================================================

async def get(self, key: str) -> str | None:
"""Get value for key."""
client = await self.get_client()
try:
return await client.get(key)
except RedisError as exc:
raise RuntimeError(f"Redis GET error for key {key}: {exc}") from exc

async def set(
self,
key: str,
value: str,
ttl: int | None = None,
) -> bool:
"""Set key to value with optional TTL.

Args:
key: Redis key
value: Value to store
ttl: Time-to-live in seconds (optional)

Returns:
True if successful
"""
client = await self.get_client()
try:
if ttl:
return bool(await client.setex(key, ttl, value))
else:
return bool(await client.set(key, value))
except RedisError as exc:
raise RuntimeError(f"Redis SET error for key {key}: {exc}") from exc

async def delete(self, *keys: str) -> int:
"""Delete one or more keys.

Returns:
Number of keys deleted
"""
client = await self.get_client()
try:
return await client.delete(*keys)
except RedisError as exc:
raise RuntimeError(f"Redis DELETE error: {exc}") from exc

async def exists(self, *keys: str) -> int:
"""Check if keys exist.

Returns:
Number of keys that exist
"""
client = await self.get_client()
try:
return await client.exists(*keys)
except RedisError as exc:
raise RuntimeError(f"Redis EXISTS error: {exc}") from exc

# ============================================================================
# JSON Operations
# ============================================================================

async def get_json(self, key: str) -> dict[str, Any] | None:
"""Get JSON value for key."""
value = await self.get(key)
if value is None:
return None
try:
return json.loads(value)
except json.JSONDecodeError:
return None

async def set_json(
self,
key: str,
value: dict[str, Any],
ttl: int | None = None,
) -> bool:
"""Set JSON value for key."""
json_str = json.dumps(value)
return await self.set(key, json_str, ttl=ttl)

# ============================================================================
# Hash Operations
# ============================================================================

async def hget(self, name: str, key: str) -> str | None:
"""Get hash field value."""
client = await self.get_client()
try:
return await client.hget(name, key)
except RedisError as exc:
raise RuntimeError(f"Redis HGET error: {exc}") from exc

async def hset(self, name: str, key: str, value: str) -> int:
"""Set hash field value."""
client = await self.get_client()
try:
return await client.hset(name, key, value)
except RedisError as exc:
raise RuntimeError(f"Redis HSET error: {exc}") from exc

async def hgetall(self, name: str) -> dict[str, str]:
"""Get all hash fields and values."""
client = await self.get_client()
try:
return dict(await client.hgetall(name))
except RedisError as exc:
raise RuntimeError(f"Redis HGETALL error: {exc}") from exc

# ============================================================================
# Lock Operations
# ============================================================================

@asynccontextmanager
async def lock(
self,
name: str,
timeout: int = 10,
blocking: bool = True,
blocking_timeout: int | None = None,
):
"""Distributed lock context manager.

Args:
name: Lock name
timeout: Lock timeout in seconds
blocking: Whether to wait for lock acquisition
blocking_timeout: Max wait time for lock (if blocking)

Usage:
async with redis_client.lock("my-lock"):
# Critical section
pass
"""
client = await self.get_client()
lock = client.lock(
name=name,
timeout=timeout,
blocking=blocking,
blocking_timeout=blocking_timeout,
)

try:
await lock.acquire()
yield lock
finally:
await lock.release()

# ============================================================================
# Health Check
# ============================================================================

async def health_check(self) -> bool:
"""Check if Redis is accessible."""
try:
client = await self.get_client()
await client.ping()
return True
except Exception:
return False


# Singleton instance
_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
"""Get or create singleton Redis client.

Required environment variables:
REDIS_URL: Redis connection URL (e.g., redis://localhost:6379/0)
REDIS_MAX_CONNECTIONS: Maximum connections (optional, default: 50)
"""
global _redis_client

if _redis_client is not None:
return _redis_client

# Use centralized resolver
from services.common.config.base_settings import resolve_env

# Primary environment variable used by most services.
redis_url = resolve_env("REDIS_URL")
if not redis_url:
raise RuntimeError("REDIS_URL environment variable not set")

max_connections = int(resolve_env("REDIS_MAX_CONNECTIONS", "50"))

_redis_client = RedisClient(
url=redis_url,
max_connections=max_connections,
)

return _redis_client
