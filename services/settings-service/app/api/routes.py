"""API endpoints for the settings service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from .schemas import (
    TenantSettings,
    TenantSummary,
    ModelProfile,
    NotificationPreferences,
    BillingLedger,
)

router = APIRouter(prefix="/v1", tags=["settings"])

TENANTS: Dict[str, TenantSettings] = {}
MODEL_PROFILES: Dict[str, ModelProfile] = {"default": ModelProfile()}
NOTIFICATION_PREFS: Dict[str, NotificationPreferences] = {}
BILLING: Dict[str, BillingLedger] = {}

# New in‑memory audit log for simplicity
AUDIT_LOGS: List[Dict[str, Any]] = []


def _tenant_or_404(tenant_id: str) -> TenantSettings:
    tenant = TENANTS.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.get("/tenants", response_model=List[TenantSummary])
def list_tenants() -> List[TenantSummary]:
    return [
        TenantSummary(tenant_id=tenant.tenant_id, display_name=tenant.display_name, deployment_mode=tenant.deployment_mode)
        for tenant in TENANTS.values()
    ]


@router.put("/tenants/{tenant_id}", response_model=TenantSettings)
def upsert_tenant(tenant_id: str, payload: TenantSettings) -> TenantSettings:
    TENANTS[tenant_id] = payload
    return payload


@router.get("/tenants/{tenant_id}", response_model=TenantSettings)
def get_tenant(tenant_id: str) -> TenantSettings:
    return _tenant_or_404(tenant_id)


@router.get("/tenants/{tenant_id}/model-profiles", response_model=List[ModelProfile])
def list_model_profiles(tenant_id: str) -> List[ModelProfile]:
    """Return all model profiles visible to the tenant.
    Currently profiles are stored globally in ``MODEL_PROFILES``; a real implementation
    would scope them per tenant and persist to a database.
    """
    _tenant_or_404(tenant_id)
    return list(MODEL_PROFILES.values())


@router.put("/tenants/{tenant_id}/model-profiles", response_model=ModelProfile)
def update_model_profile(tenant_id: str, profile: ModelProfile) -> ModelProfile:
    _tenant_or_404(tenant_id)
    MODEL_PROFILES[profile.name] = profile
    TENANTS[tenant_id].default_model_profile = profile.name
    return profile


@router.post("/tenants/{tenant_id}/model-profiles", response_model=ModelProfile, status_code=status.HTTP_201_CREATED)
def create_model_profile(tenant_id: str, profile: ModelProfile) -> ModelProfile:
    """Create a new model profile.
    If a profile with the same name exists, a conflict is raised.
    """
    _tenant_or_404(tenant_id)
    if profile.name in MODEL_PROFILES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model profile already exists")
    MODEL_PROFILES[profile.name] = profile
    AUDIT_LOGS.append({"action": "create_profile", "tenant": tenant_id, "profile": profile.name, "timestamp": datetime.utcnow()})
    return profile


@router.get("/tenants/{tenant_id}/notification-preferences", response_model=NotificationPreferences)
def get_notification_prefs(tenant_id: str) -> NotificationPreferences:
    _tenant_or_404(tenant_id)
    return NOTIFICATION_PREFS.get(tenant_id, NotificationPreferences(tenant_id=tenant_id, channels=[]))


@router.put("/tenants/{tenant_id}/notification-preferences", response_model=NotificationPreferences)
def update_notification_prefs(tenant_id: str, prefs: NotificationPreferences) -> NotificationPreferences:
    _tenant_or_404(tenant_id)
    NOTIFICATION_PREFS[tenant_id] = prefs
    return prefs


@router.get("/tenants/{tenant_id}/model-profiles/{profile_name}", response_model=ModelProfile)
def get_model_profile_by_name(tenant_id: str, profile_name: str) -> ModelProfile:
    """Return a specific model profile.

    The profiles are stored globally in ``MODEL_PROFILES``; a real implementation
    would scope them per tenant and fetch from a database.
    """
    _tenant_or_404(tenant_id)
    profile = MODEL_PROFILES.get(profile_name)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model profile not found")
    return profile


@router.delete("/tenants/{tenant_id}/model-profiles/{profile_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_profile(tenant_id: str, profile_name: str) -> None:
    """Delete a model profile.
    Removes the profile from the in‑memory store and records an audit entry.
    """
    _tenant_or_404(tenant_id)
    if profile_name not in MODEL_PROFILES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model profile not found")
    del MODEL_PROFILES[profile_name]
    AUDIT_LOGS.append({"action": "delete_profile", "tenant": tenant_id, "profile": profile_name, "timestamp": datetime.utcnow()})
    # No content returned (204)
