"""Simple in-memory rate limiter keyed by tenant and adapter."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict


@dataclass
class RateLimitExceeded(Exception):
    """Raised when a caller exceeds their allowed rate."""

    remaining_seconds: float
    limit: int

    def __str__(self) -> str:  # pragma: no cover - human readable message
        wait = max(0, round(self.remaining_seconds, 2))
        return f"Rate limit exceeded. Retry after {wait} seconds"


class RateLimiter:
    """Sliding-window rate limiter."""

    def __init__(self, default_limit: int, window_seconds: int = 60) -> None:
        self.default_limit = max(1, default_limit)
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Deque[float]] = {}

    def _prune(self, bucket: Deque[float], now: float) -> None:
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def check(self, key: str, override_limit: int | None = None) -> int:
        """Record a hit for the given key, raising if the limit is exceeded."""

        limit = max(1, override_limit or self.default_limit)
        now = time.time()
        bucket = self._buckets.setdefault(key, deque())
        self._prune(bucket, now)

        if len(bucket) >= limit:
            retry_after = bucket[0] + self.window_seconds - now
            raise RateLimitExceeded(max(0.0, retry_after), limit)

        bucket.append(now)
        return limit - len(bucket)

    def current(self, key: str) -> int:
        """Return current usage count within the window."""

        now = time.time()
        bucket = self._buckets.get(key)
        if not bucket:
            return 0
        self._prune(bucket, now)
        return len(bucket)
