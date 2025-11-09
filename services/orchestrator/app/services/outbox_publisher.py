"""
Background service to publish events from outbox table to Kafka.

Implements reliable event publishing using the outbox pattern.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from ..integrations.kafka_client import create_kafka_producer, KafkaProducer
from ..repository.outbox_event_repository import OutboxEventRepository
from ..repository.outbox import OutboxEvent

logger = logging.getLogger(__name__)


class OutboxPublisherService:
    """Service to publish events from outbox table to Kafka."""

    def __init__(
        self,
        session_factory,
        kafka_bootstrap_servers: str,
        kafka_client_id: str = "outbox-publisher",
        batch_size: int = 100,
        flush_interval: float = 1.0,
        max_retries: int = 3,
    ):
        self.session_factory = session_factory
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_client_id = kafka_client_id
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.producer: Optional[AIOKafkaProducer] = None
        self._running = False

    async def start(self) -> None:
        """Start the outbox publisher service."""
        logger.info("Starting outbox publisher service")
        self.producer = await create_kafka_producer()
        self._running = True

        # Start the processing loop
        asyncio.create_task(self._processing_loop())

    async def stop(self) -> None:
        """Stop the outbox publisher service."""
        logger.info("Stopping outbox publisher service")
        self._running = False
        if self.producer:
            await self.producer.stop()

    async def _processing_loop(self) -> None:
        """Main processing loop for publishing events."""
        while self._running:
            try:
                await self._publish_batch()
                await asyncio.sleep(self.flush_interval)
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Back off on errors

    async def _publish_batch(self) -> None:
        """Publish a batch of pending events."""
        async with self.session_factory() as session:
            repo = OutboxEventRepository(session)
            events = await repo.get_pending_events(limit=self.batch_size)

            for event in events:
                await self._publish_event(repo, event)

    async def _publish_event(self, repo: OutboxEventRepository, event: OutboxEvent) -> None:
        """Publish a single event to Kafka."""
        try:
            message = {
                "event_type": event.event_type,
                "payload": event.payload,
                "timestamp": event.created_at.isoformat(),
                "event_id": str(event.id),
            }

            logger.debug(f"Publishing event {event.id} to topic {event.topic}: {message}")

            await self.producer.send_event(
                topic=event.topic,
                message=message,
                key=event.key,
            )

            # Mark as processed
            await repo.mark_as_processed(event.id)
            await session.commit()

            logger.info(f"Successfully published event {event.id}")

        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            await self._handle_publishing_error(repo, event, str(e))
            await session.commit()

    async def _handle_publishing_error(self, repo: OutboxEventRepository, event: OutboxEvent, error: str) -> None:
        """Handle publishing errors and update retry count."""
        current_retry = int(event.retry_count) if event.retry_count else 0

        if current_retry >= self.max_retries:
            logger.error(f"Event {event.id} failed permanently after {self.max_retries} retries")
            await repo.mark_as_failed(event.id, error)
        else:
            logger.warning(f"Event {event.id} failed, retry {current_retry + 1}/{self.max_retries}")
            # Update retry count but keep pending for next attempt
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.id == event.id)
                .values(
                    retry_count=str(current_retry + 1),
                    last_error=error,
                )
            )
            await repo.session.execute(stmt)

    async def retry_failed_events(self, max_age_hours: int = 24) -> int:
        """Retry failed events within the age limit."""
        async with self.session_factory() as session:
            repo = OutboxEventRepository(session)
            count = await repo.retry_failed_events(max_age_hours)
            await session.commit()
            logger.info(f"Retried {count} failed events")
            return count


async def create_outbox_publisher_service(
    session_factory,
    kafka_bootstrap_servers: str = "localhost:9092",
) -> OutboxPublisherService:
    """Factory function to create outbox publisher service."""
    return OutboxPublisherService(
        session_factory=session_factory,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
    )
