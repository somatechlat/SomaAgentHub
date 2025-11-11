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
    """Single durable event row."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = Field(index=True)
    topic: str = Field(index=True)
    key: str | None = Field(default=None, index=True)
    payload: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = Field(default=None)
    processing_status: str = Field(default="pending")
    retry_count: str = Field(default="0")  # Store as string for compatibility
    last_error: str | None = Field(default=None)
