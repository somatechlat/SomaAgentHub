"""
Event publishing utilities for distributed event-driven architecture.

Provides multiple backends for event publishing including in-memory and Kafka.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EventPublisher(ABC):
    """Abstract base class for event publishers."""

    def __init__(self, service_name: str):
        self.service_name = service_name

    @abstractmethod
    async def publish(self, event_data: Dict[str, Any]) -> None:
        """Publish a single event."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish multiple events."""
        pass


class InMemoryEventPublisher(EventPublisher):
    """In-memory event publisher for testing and development."""

    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.events: List[Dict[str, Any]] = []

    async def publish(self, event_data: Dict[str, Any]) -> None:
        """Publish event to in-memory storage."""
        enriched_event = {
            **event_data,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
        }
        self.events.append(enriched_event)
        logger.debug(f"Published in-memory event: {event_data.get('event_type')}")

    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish multiple events to in-memory storage."""
        for event in events:
            await self.publish(event)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all published events (for testing)."""
        return self.events.copy()

    def clear(self) -> None:
        """Clear all events (for testing)."""
        self.events.clear()


class KafkaEventPublisher(EventPublisher):
    """Kafka event publisher for production use."""

    def __init__(
        self,
        service_name: str,
        kafka_config: Dict[str, Any],
        topic_prefix: str = "events",
    ):
        super().__init__(service_name)
        self.kafka_config = kafka_config
        self.topic_prefix = topic_prefix
        self._producer = None

    async def _get_producer(self):
        """Get or create Kafka producer."""
        if self._producer is None:
            try:
                from aiokafka import AIOKafkaProducer

                self._producer = AIOKafkaProducer(**self.kafka_config)
                await self._producer.start()
            except ImportError:
                logger.warning("aiokafka not available, falling back to in-memory")
                return InMemoryEventPublisher(self.service_name)
        return self._producer

    async def publish(self, event_data: Dict[str, Any]) -> None:
        """Publish event to Kafka."""
        producer = await self._get_producer()

        if isinstance(producer, InMemoryEventPublisher):
            await producer.publish(event_data)
            return

        try:
            topic = f"{self.topic_prefix}.{event_data.get('event_type', 'default')}"
            message = json.dumps(
                {
                    **event_data,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "service": self.service_name,
                }
            )

            await producer.send_and_wait(topic, message.encode("utf-8"))
            logger.info(f"Published Kafka event to {topic}: {event_data.get('event_type')}")

        except Exception as e:
            logger.error(f"Failed to publish to Kafka: {e}")
            raise

    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish multiple events to Kafka."""
        producer = await self._get_producer()

        if isinstance(producer, InMemoryEventPublisher):
            await producer.publish_batch(events)
            return

        try:
            for event in events:
                await self.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish batch to Kafka: {e}")
            raise

    async def close(self) -> None:
        """Close Kafka producer."""
        if self._producer and hasattr(self._producer, "stop"):
            await self._producer.stop()


class EventPublisherFactory:
    """Factory for creating event publishers based on configuration."""

    @staticmethod
    def create_publisher(service_name: str, backend: str = "memory", **kwargs) -> EventPublisher:
        """Create appropriate event publisher based on backend type."""

        if backend == "memory":
            return InMemoryEventPublisher(service_name)
        elif backend == "kafka":
            return KafkaEventPublisher(
                service_name=service_name,
                kafka_config=kwargs.get("kafka_config", {}),
                topic_prefix=kwargs.get("topic_prefix", "events"),
            )
        else:
            raise ValueError(f"Unknown backend: {backend}")


def get_publisher(service_name: str) -> EventPublisher:
    """Get configured event publisher for service."""
    import os

    backend = os.getenv("EVENT_BACKEND", "memory")

    if backend == "kafka":
        kafka_config = {"bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")}
        return KafkaEventPublisher(service_name, kafka_config)
    else:
        return InMemoryEventPublisher(service_name)
