"""Notification bus implementation with optional Kafka integration."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Optional

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer  # type: ignore
except ImportError:  # pragma: no cover - dependency injected via requirements
    AIOKafkaConsumer = None  # type: ignore
    AIOKafkaProducer = None  # type: ignore

from ..api.schemas import NotificationPayload, NotificationRecord
from .config import Settings

logger = logging.getLogger("notification.bus")


class NotificationBus:
    """Wrapper around Kafka for publishing and caching notifications."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._consume_task: Optional[asyncio.Task[None]] = None
        self._cache: Deque[NotificationRecord] = deque(maxlen=settings.cache_limit)
        self._lock = asyncio.Lock()

    @property
    def cache(self) -> Deque[NotificationRecord]:
        return self._cache

    async def startup(self) -> None:
        if not self._settings.use_kafka:
            logger.info("Kafka integration disabled via configuration")
            return
        if not self._settings.kafka_bootstrap_servers:
            logger.warning("Kafka bootstrap servers not configured; running in in-memory mode")
            return
        if AIOKafkaProducer is None:
            logger.error("aiokafka not installed; unable to initialise Kafka producer")
            return

        try:
            self._producer = AIOKafkaProducer(bootstrap_servers=self._settings.kafka_bootstrap_servers)
            await self._producer.start()
            logger.info("Kafka producer connected", extra={"topic": self._settings.produce_topic})
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to start Kafka producer", exc_info=exc)
            self._producer = None

        if self._settings.consume_topic and AIOKafkaConsumer is not None:
            try:
                self._consumer = AIOKafkaConsumer(
                    self._settings.consume_topic,
                    bootstrap_servers=self._settings.kafka_bootstrap_servers,
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    group_id=self._settings.consumer_group,
                )
                await self._consumer.start()
                self._consume_task = asyncio.create_task(self._consume_loop())
                logger.info(
                    "Kafka consumer subscribed",
                    extra={"topic": self._settings.consume_topic, "group": self._settings.consumer_group},
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to start Kafka consumer", exc_info=exc)
                self._consumer = None

    async def shutdown(self) -> None:
        if self._consume_task:
            self._consume_task.cancel()
            with contextlib.suppress(Exception):
                await self._consume_task
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        try:
            async for message in self._consumer:
                try:
                    data = json.loads(message.value.decode("utf-8"))
                    record = NotificationRecord(**data)
                except Exception:  # noqa: BLE001
                    logger.warning("Failed to decode notification message", exc_info=True)
                    continue
                async with self._lock:
                    self._cache.append(record)
        except asyncio.CancelledError:  # pragma: no cover - shutdown path
            pass
        except Exception as exc:  # noqa: BLE001
            logger.error("Notification consumer loop crashed", exc_info=exc)

    async def publish(self, payload: NotificationPayload) -> NotificationRecord:
        record = NotificationRecord(
            tenant_id=payload.tenant_id,
            channel=payload.channel,
            message=payload.message,
            severity=payload.severity,
            metadata=payload.metadata or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._send(record)
        async with self._lock:
            self._cache.append(record)
        return record

    async def _send(self, record: NotificationRecord) -> None:
        if self._producer is None:
            logger.debug("Kafka producer unavailable; notification cached locally", extra=record.model_dump())
            return
        try:
            await self._producer.send_and_wait(
                self._settings.produce_topic,
                json.dumps(record.model_dump()).encode("utf-8"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to publish notification", exc_info=exc)

    async def backlog(self, limit: int = 50, tenant_id: Optional[str] = None) -> list[NotificationRecord]:
        async with self._lock:
            records = list(self._cache)
        if tenant_id:
            records = [record for record in records if record.tenant_id == tenant_id]
        if limit and limit > 0:
            records = records[-limit:]
        return records


_notification_bus: Optional[NotificationBus] = None


def get_notification_bus(settings: Settings) -> NotificationBus:
    global _notification_bus
    if _notification_bus is None:
        _notification_bus = NotificationBus(settings)
    return _notification_bus
