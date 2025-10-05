"""Key management utilities for signing JWTs."""

from __future__ import annotations

import asyncio
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

try:  # pragma: no cover - redis may be absent during tests
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore[assignment]


@dataclass(slots=True)
class SigningKey:
    """In-memory representation of a signing key."""

    kid: str
    secret: str
    created_at: datetime
    expires_at: datetime

    def as_json(self) -> str:
        payload = {
            "kid": self.kid,
            "secret": self.secret,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
        return json.dumps(payload)

    @classmethod
    def from_json(cls, raw: str) -> "SigningKey":
        data = json.loads(raw)
        return cls(
            kid=data["kid"],
            secret=data["secret"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )

    def is_expired(self, at: Optional[datetime] = None) -> bool:
        now = at or datetime.now(timezone.utc)
        return now >= self.expires_at


class KeyManager:
    """Manages signing key material with optional Redis persistence."""

    def __init__(
        self,
        redis: Optional[Redis],
        *,
        rotation_interval: timedelta,
        namespace: str = "identity:keys",
        fallback_secret: Optional[str] = None,
    ) -> None:
        self._redis = redis
        self._rotation_interval = rotation_interval
        self._namespace = namespace
        self._fallback_secret = fallback_secret or secrets.token_urlsafe(64)
        self._active: Optional[SigningKey] = None
        self._lock = asyncio.Lock()
        self._cache: dict[str, SigningKey] = {}

    @property
    def _active_key(self) -> str:
        return f"{self._namespace}:active"

    def _key_entry(self, kid: str) -> str:
        return f"{self._namespace}:key:{kid}"

    async def start(self) -> SigningKey:
        key = await self._load_active()
        if key is None:
            key = await self._rotate(create_only=True)
        return key

    async def stop(self) -> None:
        return None

    async def _load_active(self) -> Optional[SigningKey]:
        if self._active and not self._active.is_expired():
            return self._active

        if self._redis is None:
            return self._active

        active_kid = await self._redis.get(self._active_key)
        if not active_kid:
            return self._active
        raw = await self._redis.get(self._key_entry(active_kid))
        if not raw:
            return None
        key = SigningKey.from_json(raw)
        self._active = key
        self._cache[active_kid] = key
        return key

    async def get_active(self) -> SigningKey:
        async with self._lock:
            key = await self._load_active()
            if key is None or self._should_rotate(key):
                key = await self._rotate()
            return key

    async def get_by_kid(self, kid: str) -> Optional[SigningKey]:
        if self._active and self._active.kid == kid:
            return self._active
        cached = self._cache.get(kid)
        if cached is not None:
            return cached
        if self._redis is None:
            return None
        raw = await self._redis.get(self._key_entry(kid))
        if not raw:
            return None
        key = SigningKey.from_json(raw)
        self._cache[kid] = key
        return key

    async def rotate_if_due(self) -> SigningKey:
        async with self._lock:
            key = await self._load_active()
            if key is None or self._should_rotate(key):
                return await self._rotate()
            return key

    def _should_rotate(self, key: SigningKey) -> bool:
        age = datetime.now(timezone.utc) - key.created_at
        return age >= self._rotation_interval

    async def _rotate(self, *, create_only: bool = False) -> SigningKey:
        now = datetime.now(timezone.utc)
        kid = uuid4().hex
        secret = self._fallback_secret if (create_only and self._redis is None) else secrets.token_urlsafe(64)
        expires_at = now + (self._rotation_interval * 2)
        key = SigningKey(kid=kid, secret=secret, created_at=now, expires_at=expires_at)
        self._active = key
        self._cache[kid] = key

        if self._redis is not None:
            await self._redis.set(self._key_entry(kid), key.as_json())
            await self._redis.set(self._active_key, kid)
        return key
