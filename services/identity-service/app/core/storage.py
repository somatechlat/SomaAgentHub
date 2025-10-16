"""Redis-backed persistence layer for the identity service."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime

from redis.asyncio import Redis

from ..api.schemas import TrainingLockStatus, UserRecord


class IdentityStore:
    """Persistence abstraction for identity data."""

    def __init__(self, client: Redis, namespace: str = "identity") -> None:
        if client is None:
            raise ValueError("IdentityStore requires a Redis client; none provided")
        self._client = client
        self._ns = namespace

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------
    def _user_key(self, user_id: str) -> str:
        return f"{self._ns}:user:{user_id}"

    @property
    def _users_index(self) -> str:
        return f"{self._ns}:users"

    def _training_key(self, tenant_id: str) -> str:
        return f"{self._ns}:training:{tenant_id}"

    def _token_key(self, jti: str) -> str:
        return f"{self._ns}:token:{jti}"

    def _constitution_key(self, tenant_id: str) -> str:
        return f"constitution:{tenant_id}"

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------
    async def upsert_user(self, record: UserRecord) -> UserRecord:
        await self._client.set(self._user_key(record.user_id), record.model_dump_json())
        await self._client.sadd(self._users_index, record.user_id)
        return record

    async def get_user(self, user_id: str) -> UserRecord | None:
        raw = await self._client.get(self._user_key(user_id))
        if raw is None:
            return None
        return UserRecord.model_validate_json(raw)

    async def list_users(self) -> Iterable[UserRecord]:
        user_ids = await self._client.smembers(self._users_index)
        results = []
        for user_id in user_ids:
            raw = await self._client.get(self._user_key(user_id))
            if raw:
                try:
                    results.append(UserRecord.model_validate_json(raw))
                except Exception:
                    continue
        return results

    # ------------------------------------------------------------------
    # Training lock management
    # ------------------------------------------------------------------
    async def set_training_lock(self, lock: TrainingLockStatus) -> TrainingLockStatus:
        await self._client.set(self._training_key(lock.tenant_id), lock.model_dump_json())
        return lock

    async def get_training_lock(self, tenant_id: str) -> TrainingLockStatus | None:
        raw = await self._client.get(self._training_key(tenant_id))
        if raw is None:
            return None
        return TrainingLockStatus.model_validate_json(raw)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------
    async def store_token_claims(self, jti: str, claims: dict, ttl_seconds: int) -> None:
        payload = json.dumps(claims)
        await self._client.setex(self._token_key(jti), ttl_seconds, payload)

    async def get_token_claims(self, jti: str) -> dict | None:
        raw = await self._client.get(self._token_key(jti))
        if raw is None:
            return None
        return json.loads(raw)

    async def revoke_token(self, jti: str) -> None:
        await self._client.delete(self._token_key(jti))

    async def token_ttl(self, jti: str) -> int | None:
        ttl = await self._client.ttl(self._token_key(jti))
        if ttl is None or ttl < 0:
            return None
        return int(ttl)

    async def get_constitution_hash(self, tenant_id: str) -> str | None:
        return await self._client.get(self._constitution_key(tenant_id))

    # ------------------------------------------------------------------
    async def ping(self) -> bool:
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        aclose = getattr(self._client, "aclose", None)
        if callable(aclose):
            await aclose()
        else:
            close = getattr(self._client, "close", None)
            if callable(close):
                result = close()
                if hasattr(result, "__await__"):
                    await result
        disconnect = getattr(self._client, "connection_pool", None)
        if disconnect and hasattr(disconnect, "disconnect"):
            result = disconnect.disconnect()
            if hasattr(result, "__await__"):
                await result


def utc_from_timestamp(timestamp: int | float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=datetime.UTC)
