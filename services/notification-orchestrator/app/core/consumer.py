"""Kafka consumer broadcasting notifications to websockets."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from aiokafka import AIOKafkaConsumer

from .config import get_settings
from ..api.routes import connections


class NotificationConsumer:
    def __init__(self) -> None:
        cfg = get_settings()
        self.consumer = AIOKafkaConsumer(
            cfg.kafka_topic,
            bootstrap_servers=cfg.kafka_bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        await self.consumer.start()
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self.consumer.stop()

    async def _loop(self) -> None:
        while self._running:
            try:
                msg = await self.consumer.getone()
            except Exception:
                await asyncio.sleep(1.0)
                continue
            await self.broadcast(msg.value)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        tenant_id = payload.get("tenant_id", "demo")
        ws_set = connections.get(tenant_id, set())
        for ws in list(ws_set):
            try:
                await ws.send_json(payload)
            except Exception:
                ws_set.discard(ws)


notification_consumer = NotificationConsumer()
