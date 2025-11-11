"""Outbox event model for durable event storage."""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression
from services.common.config.base_settings import resolve_env

# Use declarative base for compatibility with both PostgreSQL and SQLite
Base = declarative_base()


class OutboxEvent(Base):
"""SQLAlchemy model for durable event storage.

This table stores events that need to be published to external systems.
Events are processed in order and deleted after successful publication.
"""

__tablename__ = "outbox_events"

# Primary key using UUID for distributed systems compatibility
id = Column(
UUID(as_uuid=True),
primary_key=True,
default=uuid.uuid4,
server_default=expression.text("gen_random_uuid()"),
)

# Event type identifier (e.g., 'gateway.wizard_approved.v1')
event_type = Column(String(255), nullable=False, index=True)

# Event data as JSON
event_data = Column(JSON, nullable=False)

# When the event was created
created_at = Column(
DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
)

# When the event was processed (null if not yet processed)
processed_at = Column(DateTime(timezone=True), nullable=True)

# Processing status for tracking
processing_status = Column(
String(50), nullable=False, default="pending", index=True
)

# Retry count for failed publications
retry_count = Column(String(10), nullable=False, default="0")

# Optional error message from last processing attempt
last_error = Column(Text, nullable=True)

def __repr__(self) -> str:
return f"<OutboxEvent(id={self.id}, type={self.event_type}, status={self.processing_status})>"

def to_dict(self) -> Dict[str, Any]:
"""Convert model to dictionary for serialization."""
return {
"id": str(self.id),
"event_type": self.event_type,
"event_data": self.event_data,
"created_at": self.created_at.isoformat() if self.created_at else None,
"processed_at": (
self.processed_at.isoformat() if self.processed_at else None
),
"processing_status": self.processing_status,
"retry_count": int(self.retry_count),
"last_error": self.last_error,
}
