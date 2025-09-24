"""API endpoints for identity service."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from .schemas import TrainingLockRequest, TrainingLockStatus, UserRecord

router = APIRouter(prefix="/v1", tags=["identity"])


USERS: Dict[str, UserRecord] = {}
TRAINING_LOCKS: Dict[str, TrainingLockStatus] = {}


@router.get("/users", response_model=List[UserRecord])
def list_users() -> List[UserRecord]:
    return list(USERS.values())


@router.put("/users/{user_id}", response_model=UserRecord)
def upsert_user(user_id: str, payload: UserRecord) -> UserRecord:
    USERS[user_id] = payload
    return payload


@router.get("/users/{user_id}", response_model=UserRecord)
def get_user(user_id: str) -> UserRecord:
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users/{user_id}/capabilities", response_model=List[str])
def get_user_capabilities(user_id: str) -> List[str]:
    return get_user(user_id).capabilities


@router.post("/training/start", response_model=TrainingLockStatus)
def start_training(request: TrainingLockRequest) -> TrainingLockStatus:
    lock = TrainingLockStatus(
        tenant_id=request.tenant_id,
        locked=True,
        locked_by=request.requested_by,
        locked_at=datetime.utcnow(),
    )
    TRAINING_LOCKS[request.tenant_id] = lock
    return lock


@router.post("/training/stop", response_model=TrainingLockStatus)
def stop_training(request: TrainingLockRequest) -> TrainingLockStatus:
    lock = TRAINING_LOCKS.get(request.tenant_id)
    if lock is None:
        lock = TrainingLockStatus(tenant_id=request.tenant_id, locked=False)
    else:
        lock.locked = False
        lock.locked_by = request.requested_by
        lock.locked_at = datetime.utcnow()
    TRAINING_LOCKS[request.tenant_id] = lock
    return lock
