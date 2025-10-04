"""API routes serving the signed SomaGent constitution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core.config import settings
from ..core.constitution import ConstitutionRegistry, verify_bundle
from ..core.models import ConstitutionBundle, ConstitutionSummary, HashResponse, ValidationResult

router = APIRouter(prefix="/v1", tags=["constitution"])


def get_registry(request: Request) -> ConstitutionRegistry:
    registry = getattr(request.app.state, "constitution_registry", None)
    if registry is None:  # pragma: no cover - application misconfiguration
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Constitution registry unavailable")
    return registry


@router.get("/constitution/{tenant}", response_model=ConstitutionBundle)
async def get_constitution(tenant: str, registry: ConstitutionRegistry = Depends(get_registry)) -> ConstitutionBundle:
    """Return the verified constitution bundle for *tenant*."""

    return registry.get_bundle(tenant)


@router.get("/constitution/{tenant}/hash", response_model=HashResponse)
async def get_constitution_hash(tenant: str, registry: ConstitutionRegistry = Depends(get_registry)) -> HashResponse:
    hash_value = registry.get_hash(tenant)
    bundle = registry.get_bundle(tenant)
    return HashResponse(hash=hash_value, version=bundle.version, tenant=tenant)


@router.get("/constitution", response_model=ConstitutionSummary)
async def get_constitution_summary(registry: ConstitutionRegistry = Depends(get_registry)) -> ConstitutionSummary:
    bundle = registry.bundle
    return ConstitutionSummary(version=bundle.version, issued_at=bundle.issued_at, hash=bundle.hash)


@router.post("/constitution/validate", response_model=ValidationResult)
async def validate_constitution(payload: ConstitutionBundle, registry: ConstitutionRegistry = Depends(get_registry)) -> ValidationResult:
    """Validate a provided constitution bundle against the trusted public key."""

    issues: list[str] = []
    try:
        verify_bundle(payload, settings.public_key_path)
    except Exception as exc:
        issues.append(str(exc))
        return ValidationResult(valid=False, issues=issues)

    return ValidationResult(valid=True, issues=[])
