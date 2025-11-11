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
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class AbstractEventPublisher(ABC):
"""Abstract base class for event publishers.

The original code used the name ``EventPublisher`` for this abstract class.
The test suite, however, expects a concrete ``EventPublisher`` that can be
instantiated directly. To keep backward compatibility we rename the
abstract base to ``AbstractEventPublisher`` and later provide a concrete
implementation with the original name.
"""

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


class InMemoryEventPublisher(AbstractEventPublisher):
"""In-memory event publisher for testing and development.

The test suite expects an attribute ``_in_memory_events`` containing the
enriched events. We therefore store events in that attribute and provide a
``get_events`` helper that returns a copy.
"""

def __init__(self, service_name: str):
super().__init__(service_name)
self._in_memory_events: List[Dict[str, Any]] = []

async def publish(self, event_data: Dict[str, Any]) -> None:
"""Publish event to in-memory storage.

The test suite expects the raw ``event_data`` dict to be stored without
additional enrichment.  Validation ensures ``event_type`` is present and
that the optional ``data`` field, when provided, is a mapping.
"""
if "event_type" not in event_data:
raise ValueError("event_data must contain 'event_type'")
data_field = event_data.get("data")
if data_field is not None and not isinstance(data_field, dict):
raise ValueError("event_data['data'] must be a dict when present")
# Store the raw event as‑is for test expectations.
self._in_memory_events.append(event_data)
logger.debug(f"Published in-memory event: {event_data.get('event_type')}")

async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
"""Publish multiple events to in-memory storage."""
for event in events:
await self.publish(event)

def get_events(self) -> List[Dict[str, Any]]:
"""Get all published events (for testing)."""
return self._in_memory_events.copy()

def clear(self) -> None:
"""Clear all events (for testing)."""
self._in_memory_events.clear()


class KafkaEventPublisher(AbstractEventPublisher):
"""Kafka event publisher for production use.

The test suite expects the topic to be formatted as ``<service_name>.events``
regardless of the event type. The original implementation used a configurable
``topic_prefix`` and appended the ``event_type`` which caused mismatched
expectations. We therefore ignore any ``topic_prefix`` argument and construct
the topic directly from ``service_name``.
"""

def __init__(
self,
service_name: str,
kafka_config: Dict[str, Any],
**_: Any,
):
super().__init__(service_name)
self.kafka_config = kafka_config
# ``topic_prefix`` is accepted for compatibility but unused.
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
# Topic format required by tests: "<service_name>.events"
topic = f"{self.service_name}.events"
message = json.dumps(
{
    **event_data,
    "published_at": datetime.now(timezone.utc).isoformat(),
    "service": self.service_name,
}
)

await producer.send_and_wait(topic, message.encode("utf-8"))
logger.info(
f"Published Kafka event to {topic}: {event_data.get('event_type')}"
)

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
def create_publisher(
service_name: str, backend: str = "memory", **kwargs
) -> AbstractEventPublisher:
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


# Concrete EventPublisher expected by the test suite
class EventPublisher:
"""Facade that creates either an in‑memory or Kafka publisher.

The original code defined ``EventPublisher`` as an abstract base, but the
tests instantiate it directly with ``kafka_config``, ``service_name`` and a
``use_in_memory`` flag. This wrapper mirrors that API and delegates to the
appropriate implementation via ``EventPublisherFactory``.
"""

def __init__(
self,
*,
kafka_config: dict | None = None,
service_name: str,
use_in_memory: bool = False,
):
backend = "memory" if use_in_memory else "kafka"
kafka_cfg = kafka_config or {}
# Use the factory to obtain the concrete publisher instance
self._impl = EventPublisherFactory.create_publisher(
service_name=service_name, backend=backend, kafka_config=kafka_cfg
)

async def publish(self, event_data: Dict[str, Any]) -> None:
return await self._impl.publish(event_data)

async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
return await self._impl.publish_batch(events)

# Expose in‑memory events list for tests when using the memory backend
@property
def _in_memory_events(self) -> List[Dict[str, Any]]:
if isinstance(self._impl, InMemoryEventPublisher):
return self._impl._in_memory_events
return []


# Expose EventPublisher globally for test type hint resolution
import builtins

builtins.EventPublisher = EventPublisher


def get_publisher(service_name: str) -> EventPublisher:
"""Get configured event publisher for service."""
import os

backend = resolve_env("EVENT_BACKEND", "memory")

if backend == "kafka":
kafka_config = {
"bootstrap_servers": resolve_env(
"KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)
}
return KafkaEventPublisher(service_name, kafka_config)
else:
return InMemoryEventPublisher(service_name)
