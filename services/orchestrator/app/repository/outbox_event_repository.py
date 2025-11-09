"""
Repository for managing outbox events with real database integration.

Provides persistence for events using the outbox pattern for reliable delivery.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..repository.outbox import OutboxEvent


class OutboxEventRepository:
    """Repository for managing outbox events in the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        event_type: str,
        topic: str,
        key: Optional[str] = None,
        payload: dict = None,
        created_at: Optional[datetime] = None,
    ) -> OutboxEvent:
        """Create a new outbox event.

        Args:
            event_type: Type identifier for the event
            topic: Kafka topic to publish to
            key: Partition key for the event
            payload: Event data as dictionary
            created_at: Creation timestamp (defaults to now)

        Returns:
            Created OutboxEvent instance
        """
        if created_at is None:
            created_at = datetime.now(timezone.utc)

        event = OutboxEvent(
            event_type=event_type,
            topic=topic,
            key=key,
            payload=payload or {},
            created_at=created_at,
        )

        self.session.add(event)
        await self.session.flush()
        return event

    async def get_pending_events(self, limit: int = 100, max_retries: int = 3) -> List[OutboxEvent]:
        """Get pending events for processing.

        Args:
            limit: Maximum number of events to retrieve
            max_retries: Maximum retry attempts before skipping

        Returns:
            List of pending OutboxEvent instances
        """
        stmt = (
            select(OutboxEvent).where(OutboxEvent.processed_at.is_(None)).order_by(OutboxEvent.created_at).limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_event_by_id(self, event_id: str) -> Optional[OutboxEvent]:
        """Get an event by its UUID.

        Args:
            event_id: The event UUID as string

        Returns:
            OutboxEvent instance or None if not found
        """
        stmt = select(OutboxEvent).where(OutboxEvent.id == uuid.UUID(event_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_as_processed(self, event_id: uuid.UUID) -> None:
        """Mark an event as successfully processed.

        Args:
            event_id: The event UUID
        """
        stmt = update(OutboxEvent).where(OutboxEvent.id == event_id).values(processed_at=datetime.now(timezone.utc))
        await self.session.execute(stmt)

    async def mark_as_failed(self, event_id: uuid.UUID, error: str) -> None:
        """Mark an event as failed with error information.

        Args:
            event_id: The event UUID
            error: Error message
        """
        # Get current retry count
        event = await self.get_event_by_id(str(event_id))
        if not event:
            return

        current_retry = int(event.retry_count) if event.retry_count else 0

        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                processing_status="failed",
                last_error=error,
                retry_count=str(current_retry + 1),
            )
        )
        await self.session.execute(stmt)

    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[OutboxEvent]:
        """Get events by type.

        Args:
            event_type: Event type to filter by
            limit: Maximum number of events to retrieve

        Returns:
            List of OutboxEvent instances
        """
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_topic(self, topic: str, limit: int = 100) -> List[OutboxEvent]:
        """Get events by topic.

        Args:
            topic: Kafka topic to filter by
            limit: Maximum number of events to retrieve

        Returns:
            List of OutboxEvent instances
        """
        stmt = (
            select(OutboxEvent).where(OutboxEvent.topic == topic).order_by(OutboxEvent.created_at.desc()).limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_key(self, key: str, limit: int = 100) -> List[OutboxEvent]:
        """Get events by key.

        Args:
            key: Partition key to filter by
            limit: Maximum number of events to retrieve

        Returns:
            List of OutboxEvent instances
        """
        stmt = select(OutboxEvent).where(OutboxEvent.key == key).order_by(OutboxEvent.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def retry_failed_events(self, max_age_hours: int = 24) -> int:
        """Retry failed events that are within the age limit.

        Args:
            max_age_hours: Maximum age in hours for events to retry

        Returns:
            Number of events marked for retry
        """
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        stmt = (
            update(OutboxEvent)
            .where(
                OutboxEvent.processing_status == "failed",
                OutboxEvent.created_at >= cutoff_time,
            )
            .values(processing_status="pending", last_error=None)
        )

        result = await self.session.execute(stmt)
        return result.rowcount
