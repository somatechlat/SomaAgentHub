"""Key management utilities for signing JWTs (RS256 with live JWKS)."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

try:  # pragma: no cover - redis may be absent during tests
from redis.asyncio import Redis
except Exception:  # pragma: no cover
Redis = None  # type: ignore[assignment]

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from services.common.config.base_settings import resolve_env


@dataclass(slots=True)
class SigningKey:
    """In-memory representation of an RSA signing keypair."""

    kid: str
    private_pem: bytes
    public_pem: bytes
    created_at: datetime
    expires_at: datetime

    def as_json(self) -> str:
        payload = {
        "kid": self.kid,
        "private_pem": self.private_pem.decode("utf-8"),
        "public_pem": self.public_pem.decode("utf-8"),
        "created_at": self.created_at.isoformat(),
        "expires_at": self.expires_at.isoformat(),
        }
        return json.dumps(payload)

        @classmethod
    def from_json(cls, raw: str) -> SigningKey:
        data = json.loads(raw)
        return cls(
        kid=data["kid"],
        private_pem=data["private_pem"].encode("utf-8"),
        public_pem=data["public_pem"].encode("utf-8"),
        created_at=datetime.fromisoformat(data["created_at"]),
        expires_at=datetime.fromisoformat(data["expires_at"]),
        )

    def is_expired(self, at: datetime | None = None) -> bool:
        now = at or datetime.now(UTC)
        return now >= self.expires_at


        class KeyManager:
    """Manages RSA signing keys with optional Redis persistence and JWKS export."""

    def __init__(
    self,
    redis: Redis | None,
    *,
    rotation_interval: timedelta,
    namespace: str = "identity:keys",
    ) -> None:
    self._redis = redis
    self._rotation_interval = rotation_interval
    self._namespace = namespace
    self._active: SigningKey | None = None
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

    async def _load_active(self) -> SigningKey | None:
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

    async def get_by_kid(self, kid: str) -> SigningKey | None:
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
        age = datetime.now(UTC) - key.created_at
        return age >= self._rotation_interval

    async def _rotate(self, *, create_only: bool = False) -> SigningKey:
                                                                                                                    now = datetime.now(UTC)
                                                                                                                    kid = uuid4().hex
# Generate a new RSA keypair
                                                                                                                    private_key = rsa.generate_private_key(
                                                                                                                    public_exponent=65537, key_size=2048, backend=default_backend()
                                                                                                                    )
                                                                                                                    public_key = private_key.public_key()
                                                                                                                    private_pem = private_key.private_bytes(
                                                                                                                    encoding=serialization.Encoding.PEM,
                                                                                                                    format=serialization.PrivateFormat.PKCS8,
                                                                                                                    encryption_algorithm=serialization.NoEncryption(),
                                                                                                                    )
                                                                                                                    public_pem = public_key.public_bytes(
                                                                                                                    encoding=serialization.Encoding.PEM,
                                                                                                                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                                                                                                                    )
                                                                                                                    expires_at = now + (self._rotation_interval * 2)
                                                                                                                    key = SigningKey(
                                                                                                                    kid=kid,
                                                                                                                    private_pem=private_pem,
                                                                                                                    public_pem=public_pem,
                                                                                                                    created_at=now,
                                                                                                                    expires_at=expires_at,
                                                                                                                    )
                                                                                                                    self._active = key
                                                                                                                    self._cache[kid] = key

                                                                                                                    if self._redis is not None:
                                                                                                                        await self._redis.set(self._key_entry(kid), key.as_json())
                                                                                                                        await self._redis.set(self._active_key, kid)
                                                                                                                        return key

    def _pubkey_to_jwk(self, kid: str, pub: RSAPublicKey) -> dict:
        numbers = pub.public_numbers()
        n = numbers.n
        e = numbers.e

    def b64url_uint(val: int) -> str:
        b = val.to_bytes((val.bit_length() + 7) // 8, byteorder="big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

        return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": b64url_uint(n),
        "e": b64url_uint(e),
        }

    async def export_jwks(self) -> dict:
                                                                                                                                    """Export a JWKS document containing all known public keys."""
                                                                                                                                    keys: list[dict] = []
# Include the active key first
                                                                                                                                    if self._active:
                                                                                                                                        pub = serialization.load_pem_public_key(
                                                                                                                                        self._active.public_pem, backend=default_backend()
                                                                                                                                        )
                                                                                                                                        if isinstance(pub, RSAPublicKey):
                                                                                                                                            keys.append(self._pubkey_to_jwk(self._active.kid, pub))
# Include cached keys
                                                                                                                                            for kid, key in self._cache.items():
                                                                                                                                                if self._active and kid == self._active.kid:
                                                                                                                                                    continue
                                                                                                                                                    try:
                                                                                                                                                        pub = serialization.load_pem_public_key(
    key.public_pem, backend=default_backend()
    )
    if isinstance(pub, RSAPublicKey):
    keys.append(self._pubkey_to_jwk(kid, pub))
    except Exception:
        continue
        return {"keys": keys}
