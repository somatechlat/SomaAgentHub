"""Background service to publish events from outbox to Kafka.

This module implements a robust, async‑friendly background worker that reads
pending events from the ``outbox`` table and forwards them to Kafka using the
provided :class:`~common.events.publisher.EventPublisher` implementation.

All public methods are fully type‑annotated and include detailed docstrings to
facilitate observability and future extensions.
"""

import asyncio
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from ..repository.outbox import OutboxEventRepository
from common.events.publisher import EventPublisher
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class OutboxEventPublisherService:
    """Background service that reads events from the outbox and publishes to Kafka.

    The service runs in an ``asyncio`` task, periodically polling the database
    for new events.  It respects ``max_retries`` and marks events as failed when
    they cannot be delivered after the configured attempts.
    """

    def __init__(
        self,
        async_session_maker: sessionmaker,
        event_publisher: EventPublisher,
        batch_size: int = 100,
        poll_interval: float = 1.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the outbox event publisher.

        Args:
            async_session_maker: SQLAlchemy async session maker.
            event_publisher: Event publisher for sending events to Kafka.
            batch_size: Number of events to process per batch.
            poll_interval: Seconds to wait between polling attempts.
            max_retries: Maximum retry attempts for failed events.
        """
        self.async_session_maker = async_session_maker
        self.event_publisher = event_publisher
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background event publisher."""
        if self._running:
            logger.warning("Outbox event publisher is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Started outbox event publisher service")

    async def stop(self) -> None:
        """Stop the background event publisher."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped outbox event publisher service")

    async def _run(self) -> None:
        """Main processing loop for publishing events."""
        logger.info("Outbox event publisher loop started")

        while self._running:
            try:
                await self._publish_batch()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                logger.info("Outbox event publisher cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in outbox event publisher: {e}")
                await asyncio.sleep(self.poll_interval)  # Don't spin on errors

    async def _publish_batch(self) -> None:
        """Process a batch of pending events."""
        async with self.async_session_maker() as session:
            try:
                repo = OutboxEventRepository(session)

                # Get pending events
                events = await repo.get_pending_events(
                    limit=self.batch_size, max_retries=self.max_retries
                )

                if not events:
                    return  # No events to process

                logger.info(f"Processing {len(events)} outbox events")

                # Process each event
                for event in events:
                    try:
                        success = await self._publish_event(session, event)
                        if success:
                            await repo.mark_as_processed(event.id)
                        else:
                            await repo.mark_as_failed(
                                event.id, "Failed to publish to Kafka"
                            )
                    except Exception as e:
                        logger.exception(f"Failed to process event {event.id}: {e}")
                        await repo.mark_as_failed(event.id, str(e))

                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.exception(f"Error processing outbox batch: {e}")
                raise

    async def _publish_event(self, session: AsyncSession, event) -> bool:
        """Publish a single event to Kafka.

        Args:
            session: Database session
            event: OutboxEvent instance to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract topic from event type
            topic = self._get_topic_for_event_type(event.event_type)

            # Create key from event data if available
            key = self._create_event_key(event.event_data)

            # Publish the event
            await self.event_publisher.publish(
                topic=topic,
                key=key,
                event_type=event.event_type,
                payload=event.event_data,
            )

            logger.info(f"Successfully published event {event.id} to topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            return False

    def _get_topic_for_event_type(self, event_type: str) -> str:
        """Determine Kafka topic from event type.

        Args:
            event_type: The event type identifier

        Returns:
            Kafka topic name
        """
        # Map event types to topics
        topic_mapping = {
            "gateway.wizard_approved.v1": "gateway.events",
            "gateway.wizard_rejected.v1": "gateway.events",
            "orchestration.started.v1": "orchestrator.events",
            "orchestration.completed.v1": "orchestrator.events",
            "orchestration.failed.v1": "orchestrator.events",
        }

        return topic_mapping.get(event_type, "events.unknown")

    def _create_event_key(self, event_data: dict) -> str:
        """Create a Kafka key from event data.

        Args:
            event_data: The event payload

        Returns:
            Kafka key as string
        """
        # Use user_id or workflow_id as key for partitioning
        if "user_id" in event_data:
            return str(event_data["user_id"])
        elif "workflow_id" in event_data:
            return str(event_data["workflow_id"])
        else:
            return "default"

    async def force_publish(self, event_id: str) -> bool:
        """Force publish a specific event (for manual retry).

        Args:
            event_id: The event ID to force publish

        Returns:
            True if successful, False otherwise
        """
        async with self.async_session_maker() as session:
            try:
                repo = OutboxEventRepository(session)
                event = await repo.get_event_by_id(event_id)

                if not event:
                    logger.warning(f"Event {event_id} not found for force publish")
                    return False

                success = await self._publish_event(session, event)
                if success:
                    await repo.mark_as_processed(event.id)
                else:
                    await repo.mark_as_failed(event.id, "Manual retry failed")

                await session.commit()
                return success
            except Exception as e:
                await session.rollback()
                logger.exception(f"Error force publishing event {event_id}: {e}")
                return False
