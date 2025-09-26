"""API endpoints for identity service."""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List

import jwt
from fastapi import APIRouter, HTTPException, status

from ..core.config import get_settings
from .schemas import (
    MFAVerifyRequest,
    MFAEnrollResponse,
    TokenIssueRequest,
    TokenResponse,
    TrainingLockRequest,
    TrainingLockStatus,
    UserRecord,
)

router = APIRouter(prefix="/v1", tags=["identity"])

USERS: Dict[str, UserRecord] = {}
TRAINING_LOCKS: Dict[str, TrainingLockStatus] = {}

settings = get_settings()
JWT_SECRET = settings.resolve_jwt_secret()
JWT_EXP_SECONDS = 3600


def _ensure_user(user_id: str) -> UserRecord:
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return user


@router.get("/users", response_model=List[UserRecord])
def list_users() -> List[UserRecord]:
    return list(USERS.values())


@router.put("/users/{user_id}", response_model=UserRecord)
def upsert_user(user_id: str, payload: UserRecord) -> UserRecord:
    USERS[user_id] = payload
    return payload


@router.get("/users/{user_id}", response_model=UserRecord)
def get_user(user_id: str) -> UserRecord:
    return _ensure_user(user_id)


@router.get("/users/{user_id}/capabilities", response_model=List[str])
def get_user_capabilities(user_id: str) -> List[str]:
    return _ensure_user(user_id).capabilities


@router.post("/users/{user_id}/mfa/enroll", response_model=MFAEnrollResponse)
def enroll_mfa(user_id: str) -> MFAEnrollResponse:
    user = _ensure_user(user_id)
    secret = secrets.token_hex(8)
    user.mfa_secret = secret
    user.mfa_enabled = False
    USERS[user_id] = user
    return MFAEnrollResponse(user_id=user_id, secret=secret)


@router.post("/users/{user_id}/mfa/verify", response_model=UserRecord)
def verify_mfa(user_id: str, payload: MFAVerifyRequest) -> UserRecord:
    if payload.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mismatch user id")
    user = _ensure_user(user_id)
    if not user.mfa_secret or payload.code != user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    user.mfa_enabled = True
    USERS[user_id] = user
    return user


@router.post("/tokens/issue", response_model=TokenResponse)
def issue_token(payload: TokenIssueRequest) -> TokenResponse:
    user = _ensure_user(payload.user_id)
    if not user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA not enabled")
    if user.mfa_secret and payload.mfa_code != user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    if payload.capabilities:
        missing = [cap for cap in payload.capabilities if cap not in user.capabilities]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User lacks capabilities: {missing}")
    claims = {
        "sub": user.user_id,
        "tenant_id": payload.tenant_id,
        "capabilities": payload.capabilities or user.capabilities,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(claims, JWT_SECRET, algorithm="HS256")
    return TokenResponse(token=token, expires_in=JWT_EXP_SECONDS)


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
