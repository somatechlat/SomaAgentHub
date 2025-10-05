"""Training mode controller with Redis-backed locks and audit trail."""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from prometheus_client import Gauge

router = APIRouter(prefix="/v1/training", tags=["training"])

# Prometheus metrics
TRAINING_MODE_STATE = Gauge(
    "training_mode_state",
    "Current training mode state (1=enabled, 0=disabled)",
    labelnames=("tenant",),
)


class TrainingLockRequest(BaseModel):
    tenant: str
    user: str
    reason: str = ""


class TrainingLockResponse(BaseModel):
    tenant: str
    enabled: bool
    locked_by: str | None = None
    locked_at: float | None = None
    reason: str = ""


# TODO: Wire Redis client for lock state persistence
# For now, in-memory placeholder
_training_locks: dict[str, dict] = {}


async def _emit_training_audit(tenant: str, action: str, user: str, details: dict) -> None:
    """Emit training audit event to Kafka."""
    # TODO: Wire Kafka producer for training.audit topic
    event = {
        "tenant": tenant,
        "action": action,
        "user": user,
        "timestamp": time.time(),
        "details": details,
    }
    print(f"[TRAINING_AUDIT] {json.dumps(event)}")


@router.post("/enable", response_model=TrainingLockResponse)
async def enable_training_mode(req: TrainingLockRequest) -> TrainingLockResponse:
    """Enable training mode with Redis lock and audit trail."""
    # TODO: Check admin capability via Identity service
    
    # Check if already locked
    if req.tenant in _training_locks and _training_locks[req.tenant].get("enabled"):
        existing = _training_locks[req.tenant]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Training mode already enabled by {existing.get('locked_by')}",
        )
    
    lock_data = {
        "enabled": True,
        "locked_by": req.user,
        "locked_at": time.time(),
        "reason": req.reason,
    }
    
    # TODO: Persist to Redis with TTL
    _training_locks[req.tenant] = lock_data
    
    # Emit audit event
    await _emit_training_audit(
        req.tenant,
        "training.enabled",
        req.user,
        {"reason": req.reason},
    )
    
    # Update metrics
    TRAINING_MODE_STATE.labels(tenant=req.tenant).set(1)
    
    return TrainingLockResponse(tenant=req.tenant, **lock_data)


@router.post("/disable", response_model=TrainingLockResponse)
async def disable_training_mode(req: TrainingLockRequest) -> TrainingLockResponse:
    """Disable training mode with audit trail."""
    # TODO: Check admin capability via Identity service
    
    if req.tenant not in _training_locks or not _training_locks[req.tenant].get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training mode is not enabled for this tenant",
        )
    
    # Emit audit event
    await _emit_training_audit(
        req.tenant,
        "training.disabled",
        req.user,
        {"reason": req.reason, "previous_lock": _training_locks[req.tenant]},
    )
    
    # Clear lock
    _training_locks[req.tenant] = {"enabled": False}
    
    # Update metrics
    TRAINING_MODE_STATE.labels(tenant=req.tenant).set(0)
    
    return TrainingLockResponse(
        tenant=req.tenant,
        enabled=False,
        locked_by=None,
        locked_at=None,
        reason="",
    )


@router.get("/status/{tenant}", response_model=TrainingLockResponse)
async def get_training_status(tenant: str) -> TrainingLockResponse:
    """Get current training mode status for tenant."""
    lock_data = _training_locks.get(tenant, {"enabled": False})
    return TrainingLockResponse(
        tenant=tenant,
        enabled=lock_data.get("enabled", False),
        locked_by=lock_data.get("locked_by"),
        locked_at=lock_data.get("locked_at"),
        reason=lock_data.get("reason", ""),
    )
