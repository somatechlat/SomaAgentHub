"""Outbox pattern implementation for event‑driven architecture.

Provides a minimal persistence layer used by the test suite. It defines a
SQLModel ORM model, a matching Pydantic schema, and an asynchronous
repository that works with an ``AsyncSession`` fixture.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import JSON, Column, DateTime, SQLModel
from sqlmodel import Field as SQLField

# ``Base`` is used by tests to create tables via ``Base.metadata.create_all``.
Base = SQLModel.metadata


class OutboxEvent(SQLModel, table=True):
    """SQLModel ORM model for an outbox event."""

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    topic: str | None = SQLField(default=None, index=True)
    key: str | None = SQLField(default=None, index=True)
    event_data: dict[str, Any] = SQLField(sa_column=Column(JSON, nullable=False))
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True)),
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: datetime | None = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    retry_count: int = SQLField(default=0)
    last_error: str | None = SQLField(default=None)

    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:  # pragma: no cover
        return f"OutboxEvent(id={self.id}, type={self.event_type}, processed={self.processed})"


class OutboxEventModel(BaseModel):
    """Pydantic schema mirroring ``OutboxEvent`` used in tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processed: bool = False
    processed_at: datetime | None = None
    retry_count: int = 0
    last_error: str | None = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository offering CRUD operations for ``OutboxEvent``."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
