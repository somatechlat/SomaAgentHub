"""API endpoints for the settings and marketplace service."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from .schemas import (
    ModelProfile,
    NotificationPreferences,
    TenantSettings,
    TenantSummary,
)

router = APIRouter(prefix="/v1", tags=["settings"])

TENANTS: Dict[str, TenantSettings] = {}
MODEL_PROFILES: Dict[str, ModelProfile] = {"default": ModelProfile()}
NOTIFICATION_PREFS: Dict[str, NotificationPreferences] = {}
CAPSULES: Dict[str, dict] = {
    "plane_project_starter": {
        "id": "plane_project_starter",
        "version": "1.0.0",
        "summary": "Spin up Plane project, seed backlog, publish summary.",
    }
}


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


@router.get("/tenants/{tenant_id}/model-profiles", response_model=ModelProfile)
def get_model_profile(tenant_id: str) -> ModelProfile:
    tenant = _tenant_or_404(tenant_id)
    return MODEL_PROFILES.get(tenant.default_model_profile, MODEL_PROFILES["default"])


@router.put("/tenants/{tenant_id}/model-profiles", response_model=ModelProfile)
def update_model_profile(tenant_id: str, profile: ModelProfile) -> ModelProfile:
    _tenant_or_404(tenant_id)
    MODEL_PROFILES[profile.name] = profile
    TENANTS[tenant_id].default_model_profile = profile.name
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


@router.get("/marketplace/capsules")
def list_capsules() -> dict[str, List[dict[str, str]]]:
    return {"capsules": list(CAPSULES.values())}


@router.post("/marketplace/capsules")
def create_capsule(capsule: dict) -> dict:
    capsule_id = capsule.get("id")
    if not capsule_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="id required")
    CAPSULES[capsule_id] = capsule
    return capsule
