"""API endpoints for identity service."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core.config import get_settings
from ..core.key_manager import KeyManager
from ..core.audit import AuditLogger
from ..core.storage import IdentityStore, utc_from_timestamp
from .schemas import (
    MFAEnrollResponse,
    MFAVerifyRequest,
    TokenIssueRequest,
    TokenResponse,
    TokenRevokeRequest,
    TokenVerifyRequest,
    TokenVerifyResponse,
    TrainingLockRequest,
    TrainingLockStatus,
    UserRecord,
)

router = APIRouter(prefix="/v1", tags=["identity"])

settings = get_settings()
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = 3600


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


async def _fetch_user(store: IdentityStore, user_id: str) -> UserRecord:
    user = await store.get_user(user_id)
    if user is None:
        raise _not_found()
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return user


async def get_store(request: Request) -> IdentityStore:
    store = getattr(request.app.state, "identity_store", None)
    if store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Store unavailable")
    return store


async def get_key_manager(request: Request) -> KeyManager:
    key_manager = getattr(request.app.state, "key_manager", None)
    if key_manager is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Key manager unavailable")
    return key_manager


async def get_audit_logger(request: Request) -> AuditLogger:
    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Audit logger unavailable")
    return audit_logger


@router.get("/users", response_model=List[UserRecord])
async def list_users(store: IdentityStore = Depends(get_store)) -> List[UserRecord]:
    records = await store.list_users()
    return list(records)


@router.put("/users/{user_id}", response_model=UserRecord)
async def upsert_user(user_id: str, payload: UserRecord, store: IdentityStore = Depends(get_store)) -> UserRecord:
    if payload.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body user_id mismatch")
    return await store.upsert_user(payload)


@router.get("/users/{user_id}", response_model=UserRecord)
async def get_user(user_id: str, store: IdentityStore = Depends(get_store)) -> UserRecord:
    return await _fetch_user(store, user_id)


@router.get("/users/{user_id}/capabilities", response_model=List[str])
async def get_user_capabilities(user_id: str, store: IdentityStore = Depends(get_store)) -> List[str]:
    user = await _fetch_user(store, user_id)
    return user.capabilities


@router.post("/users/{user_id}/mfa/enroll", response_model=MFAEnrollResponse)
async def enroll_mfa(user_id: str, store: IdentityStore = Depends(get_store)) -> MFAEnrollResponse:
    user = await _fetch_user(store, user_id)
    secret = secrets.token_hex(8)
    user.mfa_secret = secret
    user.mfa_enabled = False
    await store.upsert_user(user)
    return MFAEnrollResponse(user_id=user_id, secret=secret)


@router.post("/users/{user_id}/mfa/verify", response_model=UserRecord)
async def verify_mfa(user_id: str, payload: MFAVerifyRequest, store: IdentityStore = Depends(get_store)) -> UserRecord:
    if payload.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mismatch user id")
    user = await _fetch_user(store, user_id)
    if not user.mfa_secret or payload.code != user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    user.mfa_enabled = True
    await store.upsert_user(user)
    return user


@router.post("/tokens/issue", response_model=TokenResponse)
async def issue_token(
    payload: TokenIssueRequest,
    store: IdentityStore = Depends(get_store),
    key_manager: KeyManager = Depends(get_key_manager),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> TokenResponse:
    user = await _fetch_user(store, payload.user_id)
    if not user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA not enabled")
    if user.mfa_secret and payload.mfa_code != user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    if payload.capabilities:
        missing = [cap for cap in payload.capabilities if cap not in user.capabilities]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User lacks capabilities: {missing}")

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=JWT_EXP_SECONDS)
    jti = uuid4().hex
    signing_key = await key_manager.get_active()
    constitution_hash = await store.get_constitution_hash(payload.tenant_id)
    claims = {
        "sub": user.user_id,
        "tenant_id": payload.tenant_id,
        "capabilities": payload.capabilities or user.capabilities,
        "exp": int(expires_at.timestamp()),
        "iat": int(issued_at.timestamp()),
        "jti": jti,
        "kid": signing_key.kid,
    }
    if constitution_hash:
        claims["constitution_hash"] = constitution_hash
    token = jwt.encode(claims, signing_key.secret, algorithm=JWT_ALGORITHM, headers={"kid": signing_key.kid})
    await store.store_token_claims(jti, claims, JWT_EXP_SECONDS)
    await audit_logger.emit(
        "token.issued",
        {
            "user_id": user.user_id,
            "tenant_id": payload.tenant_id,
            "jti": jti,
            "capabilities": claims["capabilities"],
            "expires_at": expires_at.isoformat(),
        },
    )
    return TokenResponse(token=token, expires_in=JWT_EXP_SECONDS, token_type="bearer")


@router.post("/tokens/verify", response_model=TokenVerifyResponse)
async def verify_token(
    payload: TokenVerifyRequest,
    store: IdentityStore = Depends(get_store),
    key_manager: KeyManager = Depends(get_key_manager),
) -> TokenVerifyResponse:
    try:
        header = jwt.get_unverified_header(payload.token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token header") from exc

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token missing kid")

    signing_key = await key_manager.get_by_kid(kid)
    if signing_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown signing key")

    try:
        claims = jwt.decode(payload.token, signing_key.secret, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token missing jti")

    if claims.get("kid") and claims["kid"] != kid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token kid mismatch")

    stored = await store.get_token_claims(jti)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    if payload.required_capabilities:
        missing = [cap for cap in payload.required_capabilities if cap not in claims.get("capabilities", [])]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing capabilities: {missing}")

    tenant_id = claims.get("tenant_id")
    if tenant_id:
        constitution_hash = claims.get("constitution_hash")
        current_hash = await store.get_constitution_hash(tenant_id)
        if current_hash and constitution_hash != current_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Constitution hash mismatch")

    expires_at = utc_from_timestamp(claims["exp"])
    issued_at = utc_from_timestamp(claims["iat"])

    return TokenVerifyResponse(
        valid=True,
        user_id=claims["sub"],
        tenant_id=claims["tenant_id"],
        capabilities=claims.get("capabilities", []),
        issued_at=issued_at,
        expires_at=expires_at,
        jti=jti,
    )


@router.post("/tokens/revoke")
async def revoke_token(
    payload: TokenRevokeRequest,
    store: IdentityStore = Depends(get_store),
    key_manager: KeyManager = Depends(get_key_manager),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> dict[str, bool]:
    try:
        header = jwt.get_unverified_header(payload.token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token header") from exc

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token missing kid")

    signing_key = await key_manager.get_by_kid(kid)
    if signing_key is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown signing key")

    try:
        claims = jwt.decode(
            payload.token,
            signing_key.secret,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token") from exc

    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token missing jti")

    if claims.get("kid") and claims["kid"] != kid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token kid mismatch")

    await store.revoke_token(jti)
    await audit_logger.emit(
        "token.revoked",
        {
            "tenant_id": claims.get("tenant_id"),
            "jti": jti,
            "user_id": claims.get("sub"),
        },
    )
    return {"revoked": True}


@router.post("/training/start", response_model=TrainingLockStatus)
async def start_training(request: TrainingLockRequest, store: IdentityStore = Depends(get_store)) -> TrainingLockStatus:
    lock = TrainingLockStatus(
        tenant_id=request.tenant_id,
        locked=True,
        locked_by=request.requested_by,
        locked_at=datetime.now(timezone.utc),
    )
    await store.set_training_lock(lock)
    return lock


@router.post("/training/stop", response_model=TrainingLockStatus)
async def stop_training(request: TrainingLockRequest, store: IdentityStore = Depends(get_store)) -> TrainingLockStatus:
    lock = await store.get_training_lock(request.tenant_id)
    now = datetime.now(timezone.utc)
    if lock is None:
        lock = TrainingLockStatus(tenant_id=request.tenant_id, locked=False, locked_by=request.requested_by, locked_at=now)
    else:
        lock.locked = False
        lock.locked_by = request.requested_by
        lock.locked_at = now
    await store.set_training_lock(lock)
    return lock


@router.get("/training/{tenant_id}", response_model=TrainingLockStatus)
async def get_training_lock(tenant_id: str, store: IdentityStore = Depends(get_store)) -> TrainingLockStatus:
    lock = await store.get_training_lock(tenant_id)
    if lock is None:
        return TrainingLockStatus(tenant_id=tenant_id, locked=False)
    return lock
