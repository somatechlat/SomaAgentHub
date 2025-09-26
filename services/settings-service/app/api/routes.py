"""API endpoints for the settings and marketplace service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from .schemas import (
    CapsuleInstallRequest,
    CapsuleInstallationRecord,
    CapsuleInstallationState,
    CapsuleRejectionRequest,
    CapsuleReviewRequest,
    CapsuleRollbackRequest,
    CapsuleSubmission,
    CapsuleSubmissionRequest,
    ComplianceReport,
    ModelProfile,
    NotificationPreferences,
    TenantSettings,
    TenantSummary,
    BillingEvent,
    BillingLedger,
    BillingRecordRequest,
)
from ..core.compliance import attestation_is_fresh, run_compliance_lint

router = APIRouter(prefix="/v1", tags=["settings"])

TENANTS: Dict[str, TenantSettings] = {}
MODEL_PROFILES: Dict[str, ModelProfile] = {"default": ModelProfile()}
NOTIFICATION_PREFS: Dict[str, NotificationPreferences] = {}
CAPSULES: Dict[str, CapsuleSubmission] = {}
INSTALLATIONS: Dict[Tuple[str, str], CapsuleInstallationState] = {}
BILLING: Dict[str, BillingLedger] = {}

# New in‑memory audit log for simplicity
AUDIT_LOGS: List[Dict[str, Any]] = []


def _tenant_or_404(tenant_id: str) -> TenantSettings:
    tenant = TENANTS.get(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


def _capsule_or_404(capsule_id: str) -> CapsuleSubmission:
    capsule = CAPSULES.get(capsule_id)
    if capsule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capsule not found")
    return capsule


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


@router.get("/marketplace/capsules", response_model=List[CapsuleSubmission])
def list_capsules(status_filter: str | None = Query(default=None)) -> List[CapsuleSubmission]:
    if status_filter:
        return [capsule for capsule in CAPSULES.values() if capsule.status == status_filter]
    return list(CAPSULES.values())


@router.post("/marketplace/capsules", response_model=CapsuleSubmission, status_code=status.HTTP_201_CREATED)
def submit_capsule(request: CapsuleSubmissionRequest) -> CapsuleSubmission:
    if request.id in CAPSULES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Capsule already exists")
    if not attestation_is_fresh(request.attestation.issued_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attestation expired; regenerate signature")

    compliance: ComplianceReport = run_compliance_lint(request)
    submission = CapsuleSubmission(
        id=request.id,
        version=request.version,
        summary=request.summary,
        author=request.author,
        status="pending_review" if compliance.passed else "needs_revision",
        attestation=request.attestation,
        compliance=compliance,
        submitted_at=datetime.utcnow(),
        metadata=request.metadata,
    )
    CAPSULES[submission.id] = submission
    return submission


@router.get("/marketplace/capsules/{capsule_id}", response_model=CapsuleSubmission)
def read_capsule(capsule_id: str) -> CapsuleSubmission:
    return _capsule_or_404(capsule_id)


@router.post("/marketplace/capsules/{capsule_id}/lint", response_model=CapsuleSubmission)
def relint_capsule(capsule_id: str) -> CapsuleSubmission:
    capsule = _capsule_or_404(capsule_id)
    request = CapsuleSubmissionRequest(
        id=capsule.id,
        version=capsule.version,
        summary=capsule.summary,
        author=capsule.author,
        attestation=capsule.attestation,
        metadata=capsule.metadata,
    )
    capsule.compliance = run_compliance_lint(request)
    if capsule.compliance.passed and capsule.status == "needs_revision":
        capsule.status = "pending_review"
    CAPSULES[capsule_id] = capsule
    return capsule


@router.post("/marketplace/capsules/{capsule_id}/approve", response_model=CapsuleSubmission)
def approve_capsule(capsule_id: str, review: CapsuleReviewRequest) -> CapsuleSubmission:
    capsule = _capsule_or_404(capsule_id)
    if capsule.status == "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capsule already approved")
    if not capsule.compliance.passed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Compliance issues must be resolved before approval")
    capsule.status = "approved"
    capsule.approved_at = datetime.utcnow()
    capsule.approved_by = review.reviewer
    if review.notes:
        notes = capsule.metadata.setdefault("review_notes", [])
        notes.append({"reviewer": review.reviewer, "notes": review.notes, "timestamp": datetime.utcnow().isoformat()})
    CAPSULES[capsule_id] = capsule
    return capsule


@router.post("/marketplace/capsules/{capsule_id}/reject", response_model=CapsuleSubmission)
def reject_capsule(capsule_id: str, review: CapsuleRejectionRequest) -> CapsuleSubmission:
    capsule = _capsule_or_404(capsule_id)
    capsule.status = "rejected"
    capsule.approved_at = None
    capsule.approved_by = None
    capsule.rejection_reason = review.reason
    notes = capsule.metadata.setdefault("review_notes", [])
    notes.append({"reviewer": review.reviewer, "notes": review.reason, "timestamp": datetime.utcnow().isoformat(), "type": "rejection"})
    CAPSULES[capsule_id] = capsule
    return capsule


def _installation_key(tenant_id: str, capsule_id: str) -> Tuple[str, str]:
    return tenant_id, capsule_id


def _state_for(tenant_id: str, capsule_id: str) -> CapsuleInstallationState:
    return INSTALLATIONS.setdefault(
        _installation_key(tenant_id, capsule_id),
        CapsuleInstallationState(tenant_id=tenant_id, capsule_id=capsule_id, active_version=None, history=[]),
    )


@router.get(
    "/marketplace/capsules/{capsule_id}/installations/{tenant_id}",
    response_model=CapsuleInstallationState,
)
def get_installation_state(capsule_id: str, tenant_id: str) -> CapsuleInstallationState:
    state = INSTALLATIONS.get(_installation_key(tenant_id, capsule_id))
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found")
    return state


@router.post(
    "/marketplace/capsules/{capsule_id}/install",
    response_model=CapsuleInstallationState,
    status_code=status.HTTP_202_ACCEPTED,
)
def install_capsule(capsule_id: str, request: CapsuleInstallRequest) -> CapsuleInstallationState:
    capsule = _capsule_or_404(capsule_id)
    if capsule.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Capsule must be approved before installation")
    _tenant_or_404(request.tenant_id)
    if request.version != capsule.version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version mismatch with approved capsule")
    state = _state_for(request.tenant_id, capsule_id)
    now = datetime.utcnow()

    # deactivate current active record
    for record in state.history:
        if record.status == "active":
            record.status = "superseded"

    record = CapsuleInstallationRecord(
        tenant_id=request.tenant_id,
        capsule_id=capsule_id,
        version=request.version,
        installed_by=request.installed_by,
        installed_at=now,
        status="active",
    )
    state.history.append(record)
    state.active_version = request.version
    INSTALLATIONS[_installation_key(request.tenant_id, capsule_id)] = state
    return state


@router.post(
    "/marketplace/capsules/{capsule_id}/rollback",
    response_model=CapsuleInstallationState,
)
def rollback_capsule(capsule_id: str, request: CapsuleRollbackRequest) -> CapsuleInstallationState:
    _tenant_or_404(request.tenant_id)
    state = INSTALLATIONS.get(_installation_key(request.tenant_id, capsule_id))
    if state is None or not state.history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No installation history")
    if len(state.history) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No previous version to rollback to")

    # mark current active as rolled back
    current = state.history[-1]
    if current.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active version to rollback")
    current.status = "rolled_back"
    rollback_note = {
        "actor": request.requested_by,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "rollback",
        "from_version": current.version,
    }
    current.metadata.setdefault("events", []).append(rollback_note)

    # find previous compatible version
    for record in reversed(state.history[:-1]):
        if record.status in {"superseded", "rolled_back", "active"}:
            record.status = "active"
            state.active_version = record.version
            INSTALLATIONS[_installation_key(request.tenant_id, capsule_id)] = state
            return state

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rollback target not found")


def _ledger_for(tenant_id: str) -> BillingLedger:
    ledger = BILLING.get(tenant_id)
    if ledger is None:
        ledger = BillingLedger(tenant_id=tenant_id, total_tokens=0, total_cost_usd=0.0, events=[])
        BILLING[tenant_id] = ledger
    return ledger


@router.post("/billing/events", response_model=BillingLedger, status_code=status.HTTP_201_CREATED)
def record_billing_event(request: BillingRecordRequest) -> BillingLedger:
    _tenant_or_404(request.tenant_id)
    event = BillingEvent(
        event_id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        capsule_id=request.capsule_id,
        tokens=request.tokens,
        cost_usd=request.cost_usd,
        recorded_at=datetime.utcnow(),
        recorded_by=request.recorded_by,
        metadata=request.metadata,
    )
    ledger = _ledger_for(request.tenant_id)
    ledger.total_tokens += request.tokens
    ledger.total_cost_usd = round(ledger.total_cost_usd + request.cost_usd, 4)
    ledger.events.append(event)
    return ledger


@router.get("/billing/ledgers/{tenant_id}", response_model=BillingLedger)
def read_billing_ledger(tenant_id: str) -> BillingLedger:
    return _ledger_for(tenant_id)


@router.get("/billing/ledgers/{tenant_id}/export", response_class=PlainTextResponse)
def export_billing_ledger(tenant_id: str) -> PlainTextResponse:
    ledger = _ledger_for(tenant_id)
    rows = ["event_id,tenant_id,capsule_id,tokens,cost_usd,recorded_at,recorded_by"]
    for event in ledger.events:
        rows.append(
            f"{event.event_id},{event.tenant_id},{event.capsule_id or ''},{event.tokens},{event.cost_usd:.4f},{event.recorded_at.isoformat()},{event.recorded_by}"
        )
    csv = "\n".join(rows)
    return PlainTextResponse(content=csv)


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
