"""Pydantic schemas for the notification orchestrator."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class NotificationPayload(BaseModel):
    tenant_id: str = Field(
        ..., description="Tenant identifier receiving the notification"
    )
    channel: str = Field(..., description="Logical channel or topic")
    message: str = Field(..., description="Notification body displayed to operators")
    severity: Literal["info", "warning", "error", "critical"] = "info"
    metadata: dict[str, str] | None = Field(
        default=None, description="Additional structured metadata"
    )


class NotificationRecord(BaseModel):
    tenant_id: str
    channel: str
    message: str
    severity: str
    metadata: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime


class EnqueueNotificationResponse(BaseModel):
    status: str
    record: NotificationRecord


class NotificationBacklogResponse(BaseModel):
    generated_at: datetime
    tenant_id: str | None
    results: list[NotificationRecord]
