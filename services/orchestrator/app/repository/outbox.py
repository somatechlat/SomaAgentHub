"""Durable outbox table for domain events.

Ensures at-least-once delivery via background worker or CDC pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import JSON, Column, String
from sqlmodel import Field, SQLModel
from services.common.config.base_settings import resolve_env


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
