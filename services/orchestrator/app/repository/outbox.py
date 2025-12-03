"""Durable outbox table for domain events.

Ensures at-least-once delivery via background worker or CDC pipeline.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column, select, update
from sqlmodel import Field, SQLModel


class OutboxEvent(SQLModel, table=True):
    """Durable outbox event model aligned with test expectations.

    Tests construct ``OutboxEvent`` with the following keyword arguments:
        ``event_type``, ``aggregate_id``, ``event_data``, ``created_at`` and optional
        ``processed`` / ``retry_count`` fields. This model therefore provides matching
        columns while preserving additional fields used in production.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = Field(index=True)
    # Identifier of the originating aggregate (e.g., wizard session ID)
    aggregate_id: str = Field(index=True)
    # Raw JSON payload of the event
    event_data: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # Processing status flags used by tests
    processed: bool = Field(default=False, index=True)
    processed_at: datetime | None = Field(default=None)
    retry_count: int = Field(default=0)
    last_error: str | None = Field(default=None)


# Repository for managing outbox events used in orchestrator tests.
class OutboxRepository:
    """Async repository providing basic CRUD for ``OutboxEvent``.

    The test suite expects methods similar to the common ``OutboxRepository``
    implementation, but operates on the ``OutboxEvent`` model defined in this
    module.
    """

    def __init__(self, session):
        self.session = session

    async def get_unprocessed_events(self, limit: int = 100):
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed == False)  # noqa: E712
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str, limit: int = 100):
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_event(self, event_id: uuid.UUID):
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_processed(self, event_id: uuid.UUID):
        stmt = (
            update(OutboxEvent).where(OutboxEvent.id == event_id).values(processed=True, processed_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str):
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self.session.execute(stmt)


# Alias to match test expectations
OutboxEventRepository = OutboxRepository
