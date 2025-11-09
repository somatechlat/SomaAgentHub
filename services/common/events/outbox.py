"""
Outbox pattern implementation for event-driven architecture.

Provides persistence layer for events before they are published to external systems.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class OutboxEvent(Base):
    """Database model for outbox events."""

    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(255), nullable=False, index=True)
    aggregate_id = Column(String(255), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)

    def __repr__(self) -> str:
        return f"OutboxEvent(id={self.id}, event_type={self.event_type}, processed={self.processed})"


class OutboxEventModel(BaseModel):
    """Pydantic model for outbox events."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Repository for managing outbox events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        """Save an event to the outbox."""
        self.session.add(event)
        await self.session.flush()
        return event

    async def save_event_model(self, event_model: OutboxEventModel) -> OutboxEvent:
        """Save an event from Pydantic model to database."""
        event = OutboxEvent(
            id=event_model.id,
            event_type=event_model.event_type,
            aggregate_id=event_model.aggregate_id,
            event_data=event_model.event_data,
            created_at=event_model.created_at,
            processed=event_model.processed,
            processed_at=event_model.processed_at,
            retry_count=event_model.retry_count,
            last_error=event_model.last_error,
        )
        return await self.save_event(event)

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        """Get unprocessed events for publishing."""
        from sqlalchemy import select

        stmt = select(OutboxEvent).where(OutboxEvent.processed == False).order_by(OutboxEvent.created_at).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        """Get events by type."""
        from sqlalchemy import select

        stmt = select(OutboxEvent).where(OutboxEvent.event_type == event_type).order_by(OutboxEvent.created_at)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_event(self, event_id: uuid.UUID) -> Optional[OutboxEvent]:
        """Get a specific event by ID."""
        from sqlalchemy import select

        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        """Mark an event as processed."""
        from sqlalchemy import update

        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )

        await self.session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        """Mark an event as failed with error information."""
        from sqlalchemy import update

        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )

        await self.session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        """Get all events for a specific aggregate."""
        from sqlalchemy import select

        stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id).order_by(OutboxEvent.created_at)

        result = await self.session.execute(stmt)
        return result.scalars().all()
