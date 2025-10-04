"""Notification orchestrator API routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.bus import NotificationBus, get_notification_bus
from ..core.config import settings
from .schemas import (
    EnqueueNotificationResponse,
    NotificationBacklogResponse,
    NotificationPayload,
)

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


async def get_bus() -> NotificationBus:
    bus = get_notification_bus(settings)
    if bus is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Notification bus unavailable")
    return bus


@router.post("", response_model=EnqueueNotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_notification(
    payload: NotificationPayload,
    bus: NotificationBus = Depends(get_bus),
) -> EnqueueNotificationResponse:
    record = await bus.publish(payload)
    return EnqueueNotificationResponse(status="queued", record=record)


@router.get("/backlog", response_model=NotificationBacklogResponse)
async def get_notification_backlog(
    limit: int = Query(default=50, ge=1, le=settings.cache_limit),
    tenant_id: str | None = Query(default=None),
    bus: NotificationBus = Depends(get_bus),
) -> NotificationBacklogResponse:
    records = await bus.backlog(limit=limit, tenant_id=tenant_id)
    return NotificationBacklogResponse(
        generated_at=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        results=records,
    )
