        ributed rate limiting service with Redis backend.

         module provides:
             - Token bucket rate limiting
             - Sliding window rate limiting
             - User-based and IP-based limits
             - Distributed rate limiting across multiple instances
             - Configurable limits per endpoint/operation
             """

             from __future__ import annotations

             import asyncio
             import hashlib
             import time
             from typing import Dict, Optional, Tuple
             from dataclasses import dataclass

             import redis.asyncio as redis
             from fastapi import HTTPException, status
             from prometheus_client import Counter, Histogram

             from ..core.config import get_settings
             from services.common.config.base_settings import resolve_env

             settings = get_settings()

             te limiting metrics
             rate_limiter_requests = Counter(
             "rate_limiter_requests_total",
             "Total rate limiter requests",
             ["client_id", "endpoint", "status"],
             )

             rate_limiter_wait_time = Histogram(
             "rate_limiter_wait_time_seconds",
             "Rate limiter wait time",
             ["client_id", "endpoint"],
             )


             @dataclass
             class RateLimitConfig:
            """Configuration for rate limiting."""

            requests_per_minute: int = 60
            requests_per_hour: int = 1000
            burst_capacity: int = 10
            window_size: int = 60  # seconds
            distributed: bool = True


            class RateLimiter:
                """Redis-backed distributed rate limiter."""

                def __init__(self, redis_url: str = None):
                    self.redis_url = redis_url or settings.redis_url or "redis://redis:6379/0"
                    self.redis = None
                    self.configs: Dict[str, RateLimitConfig] = {}

                    async def initialize(self):
                        """Initialize Redis connection."""
                        self.redis = redis.from_url(self.redis_url)

                        async def close(self):
                            """Close Redis connection."""
                            if self.redis:
                                await self.redis.close()

                                def add_config(self, endpoint: str, config: RateLimitConfig):
                                    """Add rate limit configuration for an endpoint."""
                                    self.configs[endpoint] = config

                                    def _get_client_key(self, client_id: str, endpoint: str) -> str:
                                        """Generate Redis key for client/endpoint combination."""
                                        return f"rate_limit:{endpoint}:{client_id}"

                                        async def check_rate_limit(
                                        self, client_id: str, endpoint: str = "default", increment: bool = True
                                        ) -> Tuple[bool, int]:
                                            """
                                            Check if request is within rate limits.

                                            Returns:
                                                Tuple of (is_allowed, retry_after_seconds)
                                                """
                                                config = self.configs.get(endpoint, RateLimitConfig())

                                                if not self.redis:
                                                    await self.initialize()

                                                    key = self._get_client_key(client_id, endpoint)
                                                    now = int(time.time())
                                                    window_start = now - config.window_size

                                                    e Redis pipeline for atomic operations
                                                    pipe = self.redis.pipeline()

                                                    move old entries
                                                    pipe.zremrangebyscore(key, 0, window_start)

                                                    unt current requests in window
                                                    pipe.zcard(key)

                                                    if increment:
                                                        d current request
                                                        pipe.zadd(key, {str(now): now})
                                                        pipe.expire(key, config.window_size)

                                                        results = await pipe.execute()
                                                        current_requests = results[1]

                                                        is_allowed = current_requests < config.requests_per_minute
                                                        retry_after = 0

                                                        if not is_allowed:
                                                            lculate when next request will be allowed
                                                            oldest_requests = await self.redis.zrange(key, 0, 0, withscores=True)
                                                            if oldest_requests:
                                                                oldest_time = int(oldest_requests[0][1])
                                                                retry_after = max(0, config.window_size - (now - oldest_time))

                                                                cord metrics
                                                                rate_limiter_requests.labels(
                                                                client_id=client_id,
                                                                endpoint=endpoint,
                                                                status="allowed" if is_allowed else "denied",
                                                                ).inc()

                                                                return is_allowed, retry_after

                                                                async def wait_for_rate_limit(self, client_id: str, endpoint: str = "default"):
                                                                    """
                                                                    Wait until rate limit allows the request.
                                                                    Raises HTTPException if limit exceeded.
                                                                    """
                                                                    is_allowed, retry_after = await self.check_rate_limit(client_id, endpoint)

                                                                    if not is_allowed:
                                                                        raise HTTPException(
                                                                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                                                        detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                                                                        headers={"Retry-After": str(retry_after)},
                                                                        )

                                                                        async def get_rate_limit_info(
                                                                        self, client_id: str, endpoint: str = "default"
                                                                        ) -> Dict[str, any]:
                                                                            """Get current rate limit status."""
                                                                            config = self.configs.get(endpoint, RateLimitConfig())
                                                                            is_allowed, retry_after = await self.check_rate_limit(
                                                                            client_id, endpoint, increment=False
                                                                            )

                                                                            key = self._get_client_key(client_id, endpoint)
                                                                            current_count = await self.redis.zcard(key)

                                                                            return {
                                                                            "allowed": is_allowed,
                                                                            "current_requests": current_count,
                                                                            "limit": config.requests_per_minute,
                                                                            "reset_time": int(time.time()) + retry_after if retry_after > 0 else 0,
                                                                            "window_size": config.window_size,
                                                                            }

                                                                            async def reset_rate_limit(self, client_id: str, endpoint: str = "default") -> bool:
                                                                                """Reset rate limit for a client/endpoint."""
                                                                                key = self._get_client_key(client_id, endpoint)
                                                                                deleted = await self.redis.delete(key)
                                                                                return deleted > 0


                                                                                class AdvancedRateLimiter(RateLimiter):
                                                                                    """Advanced rate limiter with multiple algorithms."""

                                                                                    async def token_bucket_check(
                                                                                    self, client_id: str, endpoint: str = "default"
                                                                                    ) -> Tuple[bool, int]:
                                                                                        """Token bucket algorithm implementation."""
                                                                                        config = self.configs.get(endpoint, RateLimitConfig())
                                                                                        key = f"token_bucket:{endpoint}:{client_id}"

                                                                                        pipe = self.redis.pipeline()
                                                                                        pipe.get(f"{key}:tokens")
                                                                                        pipe.get(f"{key}:last_refill")
                                                                                        pipe.ttl(f"{key}:tokens")

                                                                                        results = await pipe.execute()
                                                                                        tokens = int(results[0] or config.burst_capacity)
                                                                                        last_refill = float(results[1] or time.time())
                                                                                        ttl = int(results[2] or config.window_size)

                                                                                        now = time.time()
                                                                                        time_elapsed = now - last_refill
                                                                                        tokens_to_add = int(time_elapsed * (config.requests_per_minute / 60))

                                                                                        new_tokens = min(tokens + tokens_to_add, config.burst_capacity)

                                                                                        if new_tokens > 0:
                                                                                            new_tokens -= 1
                                                                                            is_allowed = True
                                                                                            retry_after = 0
                                                                                            else:
                                                                                                is_allowed = False
                                                                                                retry_after = int(60 / config.requests_per_minute)

                                                                                                date state
                                                                                                pipe.set(f"{key}:tokens", new_tokens, ex=config.window_size)
                                                                                                pipe.set(f"{key}:last_refill", now, ex=config.window_size)
                                                                                                await pipe.execute()

                                                                                                return is_allowed, retry_after


                                                                                                obal rate limiter instance
                                                                                                rate_limiter = RateLimiter()
                                                                                                advanced_rate_limiter = AdvancedRateLimiter()

                                                                                                e-configured rate limits
                                                                                                rate_limiter.add_config(
                                                                                                "api/v1/orchestrate",
                                                                                                RateLimitConfig(requests_per_minute=100, requests_per_hour=1000, burst_capacity=20),
                                                                                                )

                                                                                                rate_limiter.add_config(
                                                                                                "api/v1/health",
                                                                                                RateLimitConfig(
                                                                                                requests_per_minute=1000, requests_per_hour=10000, burst_capacity=50
                                                                                                ),
                                                                                                )

                                                                                                rate_limiter.add_config(
                                                                                                "api/v1/metrics",
                                                                                                RateLimitConfig(requests_per_minute=500, requests_per_hour=5000, burst_capacity=10),
                                                                                                )


                                                                                                te limiting middleware
                                                                                                class RateLimitMiddleware:
                                                                                                    """FastAPI middleware for rate limiting."""

                                                                                                    def __init__(self, rate_limiter_instance: RateLimiter = None):
                                                                                                        self.rate_limiter = rate_limiter_instance or rate_limiter

                                                                                                        async def __call__(self, request, call_next):
                                                                                                            """Rate limit middleware."""
                                                                                                            termine client ID
                                                                                                            client_ip = request.client.host if request.client else "unknown"
                                                                                                            user_agent = request.headers.get("user-agent", "unknown")
                                                                                                            client_id = hashlib.md5(f"{client_ip}:{user_agent}".encode()).hexdigest()

                                                                                                            e endpoint path as rate limit key
                                                                                                            endpoint = request.url.path

                                                                                                            try:
                                                                                                                await self.rate_limiter.wait_for_rate_limit(client_id, endpoint)
                                                                                                                response = await call_next(request)

                                                                                                                d rate limit headers
                                                                                                                rate_info = await self.rate_limiter.get_rate_limit_info(client_id, endpoint)
                                                                                                                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                                                                                                                response.headers["X-RateLimit-Remaining"] = str(
                                                                                                                max(0, rate_info["limit"] - rate_info["current_requests"])
                                                                                                                )
                                                                                                                response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

                                                                                                                return response

                                                                                                                except HTTPException as e:
                                                                                                                    d rate limit headers even on failure
                                                                                                                    rate_info = await self.rate_limiter.get_rate_limit_info(client_id, endpoint)
                                                                                                                    e.headers = {
                                                                                                                    "X-RateLimit-Limit": str(rate_info["limit"]),
                                                                                                                    "X-RateLimit-Remaining": str(
                                                                                                                    max(0, rate_info["limit"] - rate_info["current_requests"])
                                                                                                                    ),
                                                                                                                    "X-RateLimit-Reset": str(rate_info["reset_time"]),
                                                                                                                    **e.headers,
                                                                                                                    }
                                                                                                                    raise
