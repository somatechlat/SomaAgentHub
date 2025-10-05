"""Audit logging utilities for identity events."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency in tests
    from aiokafka import AIOKafkaProducer
except Exception:  # pragma: no cover
    AIOKafkaProducer = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AuditLogger:
    """Emit audit events to Kafka when configured, or log locally."""

    def __init__(self, bootstrap_servers: Optional[str], topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        if not self._bootstrap_servers or AIOKafkaProducer is None:
            return
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers.split(","))
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        record = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        line = json.dumps(record)

        if self._producer is None:
            logger.info("AUDIT %s", line)
            return

        try:
            await self._producer.send_and_wait(self._topic, line.encode("utf-8"))
        except Exception as exc:  # pragma: no cover - avoid crashing on audit failure
            logger.warning("Failed to emit audit event: %s", exc)
            logger.debug("Audit payload=%s", line)
