"""Redis-backed queue utilities for SLM service."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

import redis.asyncio as redis

from .config import Settings, get_settings


class QueueManager:
    """Handles enqueueing requests and storing results using Redis streams."""

    def __init__(self, redis_client: redis.Redis, settings: Settings | None = None) -> None:
        self.redis = redis_client
        self.settings = settings or get_settings()
        self.stream = self.settings.request_stream
        self.result_prefix = self.settings.result_prefix

    async def enqueue(self, payload: Dict[str, Any]) -> str:
        request_id = payload.setdefault("request_id", str(uuid.uuid4()))
        await self.redis.xadd(self.stream, {"data": json.dumps(payload)})
        return request_id

    async def store_result(self, request_id: str, result: Dict[str, Any]) -> None:
        key = f"{self.result_prefix}{request_id}"
        await self.redis.set(key, json.dumps(result), ex=3600)

    async def fetch_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        key = f"{self.result_prefix}{request_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None


class QueueWorker:
    """Background worker consuming Redis stream and invoking providers."""

    def __init__(
        self,
        redis_client: redis.Redis,
        provider_registry,
        settings: Settings | None = None,
    ) -> None:
        self.redis = redis_client
        self.provider_registry = provider_registry
        self.settings = settings or get_settings()
        self.stream = self.settings.request_stream
        self._running = False

    async def run_forever(self) -> None:
        self._running = True
        last_id = "$"
        while self._running:
            try:
                entries = await self.redis.xread(
                    {self.stream: last_id},
                    block=self.settings.stream_block_ms,
                    count=1,
                )
            except Exception:  # noqa: BLE001
                await asyncio.sleep(1.0)
                continue

            if not entries:
                continue

            _, messages = entries[0]
            for msg_id, fields in messages:
                last_id = msg_id
                payload_raw = fields.get("data")
                if not payload_raw:
                    continue
                try:
                    payload = json.loads(payload_raw)
                except json.JSONDecodeError:
                    continue

                request_id = payload.get("request_id") or str(uuid.uuid4())
                provider_name = payload.get("provider") or self.settings.default_provider
                model = payload.get("model")
                mode = payload.get("mode", "infer_sync")

                provider = self.provider_registry(provider_name)

                try:
                    if mode == "embedding":
                        result = await provider.embedding(payload)
                    else:
                        result = await provider.infer_sync(payload)
                except Exception as exc:  # noqa: BLE001
                    result = {
                        "status": "error",
                        "error": str(exc),
                        "provider": provider_name,
                        "mode": mode,
                    }

                result.setdefault("provider", provider_name)
                result.setdefault("model", model or provider_name)
                result.setdefault("status", "completed")
                await self.redis.set(
                    f"{self.settings.result_prefix}{request_id}",
                    json.dumps(result),
                    ex=3600,
                )
                await self.redis.xdel(self.stream, msg_id)

    def stop(self) -> None:
        self._running = False
