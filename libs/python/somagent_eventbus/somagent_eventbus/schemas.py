"""Typed schemas for Kafka topics."""

from datetime import datetime

from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    """Generic envelope for agent-related events."""

    event_id: str = Field(..., description="Unique identifier for the event")
    topic: str = Field(..., description="Kafka topic where the event is published")
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)
