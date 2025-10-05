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


# Redis client for persistent lock state
try:
    from services.common.redis_client import get_redis_client
    _redis_client = get_redis_client()
    _use_redis = True
except Exception as exc:
    print(f"[REDIS_WARNING] Redis client unavailable, using in-memory locks: {exc}")
    _redis_client = None
    _use_redis = False
    _training_locks: dict[str, dict] = {}


async def _emit_training_audit(tenant: str, action: str, user: str, details: dict) -> None:
    """Emit training audit event to Kafka."""
    try:
        from services.common.kafka_client import get_kafka_client
        kafka_client = get_kafka_client()
        
        # Ensure producer is started
        if kafka_client._producer is None:
            await kafka_client.start()
        
        await kafka_client.send_event(
            topic="training.audit",
            event={
                "tenant": tenant,
                "action": action,
                "user": user,
                "timestamp": time.time(),
                "details": details,
            },
            key=tenant,
        )
    except Exception as exc:
        # Log error but don't block request
        print(f"[KAFKA_ERROR] Failed to emit training audit event: {exc}")
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
    # Check admin capability via Identity service
    try:
        from services.common.identity_client import get_identity_client
        identity_client = get_identity_client()
        has_admin = await identity_client.check_user_capability(
            user_id=req.user,
            capability="training.admin",
            tenant_id=req.tenant,
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User lacks training.admin capability",
            )
    except RuntimeError as exc:
        # If identity service unavailable, log warning and continue (dev mode)
        print(f"[IDENTITY_WARNING] Admin check skipped: {exc}")
    
    # Check if already locked
    if _use_redis:
        redis_key = f"training:lock:{req.tenant}"
        existing = await _redis_client.get_json(redis_key)
        if existing and existing.get("enabled"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Training mode already enabled by {existing.get('locked_by')}",
            )
    else:
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
    
    # Persist to Redis with TTL
    if _use_redis:
        redis_key = f"training:lock:{req.tenant}"
        await _redis_client.set_json(redis_key, lock_data, ttl=86400)  # 24 hour TTL
    else:
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
    # Check admin capability via Identity service
    try:
        from services.common.identity_client import get_identity_client
        identity_client = get_identity_client()
        has_admin = await identity_client.check_user_capability(
            user_id=req.user,
            capability="training.admin",
            tenant_id=req.tenant,
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User lacks training.admin capability",
            )
    except RuntimeError as exc:
        # If identity service unavailable, log warning and continue (dev mode)
        print(f"[IDENTITY_WARNING] Admin check skipped: {exc}")
    
    if _use_redis:
        redis_key = f"training:lock:{req.tenant}"
        existing = await _redis_client.get_json(redis_key)
        if not existing or not existing.get("enabled"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training mode is not enabled for this tenant",
            )
        previous_lock = existing
    else:
        if req.tenant not in _training_locks or not _training_locks[req.tenant].get("enabled"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training mode is not enabled for this tenant",
            )
        previous_lock = _training_locks[req.tenant]
    
    # Emit audit event
    await _emit_training_audit(
        req.tenant,
        "training.disabled",
        req.user,
        {"reason": req.reason, "previous_lock": previous_lock},
    )
    
    # Clear lock
    if _use_redis:
        redis_key = f"training:lock:{req.tenant}"
        await _redis_client.delete(redis_key)
    else:
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
    if _use_redis:
        redis_key = f"training:lock:{tenant}"
        lock_data = await _redis_client.get_json(redis_key)
        if lock_data is None:
            lock_data = {"enabled": False}
    else:
        lock_data = _training_locks.get(tenant, {"enabled": False})
    
    return TrainingLockResponse(
        tenant=tenant,
        enabled=lock_data.get("enabled", False),
        locked_by=lock_data.get("locked_by"),
        locked_at=lock_data.get("locked_at"),
        reason=lock_data.get("reason", ""),
    )
