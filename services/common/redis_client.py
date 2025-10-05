"""Shared Redis client for SomaGent platform.

Provides connection pooling, async operations, and common patterns
for Redis usage across services (caching, locks, pub/sub).
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    Redis = None
    RedisError = Exception


class RedisClient:
    """Async Redis client with connection pooling."""

    def __init__(
        self,
        url: str,
        max_connections: int = 50,
        decode_responses: bool = True,
    ):
        """Initialize Redis client.
        
        Args:
            url: Redis connection URL (e.g., redis://localhost:6379/0)
            max_connections: Maximum connections in pool
            decode_responses: Auto-decode bytes to strings
        """
        if redis is None:
            raise RuntimeError("redis library not installed. Run: pip install redis[asyncio]")
        
        self.url = url
        self._pool = redis.ConnectionPool.from_url(
            url,
            max_connections=max_connections,
            decode_responses=decode_responses,
        )
        self._client: Optional[Redis] = None

    async def get_client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()

    # ============================================================================
    # Key-Value Operations
    # ============================================================================

    async def get(self, key: str) -> Optional[str]:
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
        ttl: Optional[int] = None,
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
                return await client.setex(key, ttl, value)
            else:
                return await client.set(key, value)
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

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
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
        value: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set JSON value for key."""
        json_str = json.dumps(value)
        return await self.set(key, json_str, ttl=ttl)

    # ============================================================================
    # Hash Operations
    # ============================================================================

    async def hget(self, name: str, key: str) -> Optional[str]:
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

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields and values."""
        client = await self.get_client()
        try:
            return await client.hgetall(name)
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
        blocking_timeout: Optional[int] = None,
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
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or create singleton Redis client.
    
    Required environment variables:
        REDIS_URL: Redis connection URL (e.g., redis://localhost:6379/0)
        REDIS_MAX_CONNECTIONS: Maximum connections (optional, default: 50)
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable not set")
    
    max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    _redis_client = RedisClient(
        url=redis_url,
        max_connections=max_connections,
    )
    
    return _redis_client
