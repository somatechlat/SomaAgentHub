"""API routes serving the signed SomaGent constitution and signing helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.constitution import ConstitutionRegistry, verify_bundle
from ..core.models import ConstitutionBundle, ConstitutionSummary, HashResponse, ValidationResult
from ..core.signing import ManifestSigner

router = APIRouter(prefix="/v1", tags=["constitution"])


def get_registry(request: Request) -> ConstitutionRegistry:
    registry = getattr(request.app.state, "constitution_registry", None)
    if registry is None:  # pragma: no cover - application misconfiguration
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Constitution registry unavailable")
    return registry


def get_manifest_signer(request: Request) -> ManifestSigner:
    signer = getattr(request.app.state, "manifest_signer", None)
    if signer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Manifest signing temporarily unavailable",
        )
    return signer


class ManifestSigningRequest(BaseModel):
    """Payload wrapper for persona manifest signing."""

    manifest: Dict[str, Any] = Field(..., description="Persona manifest payload to sign")


class ManifestSignatureResponse(BaseModel):
    """Response body after signing the manifest."""

    algorithm: str
    signature: str
    public_key: str
    digest: str = Field(..., description="SHA3-256 digest of the canonical manifest")
    signed_at: datetime


@router.get("/constitution/{tenant}", response_model=ConstitutionBundle)
async def get_constitution(tenant: str, registry: ConstitutionRegistry = Depends(get_registry)) -> ConstitutionBundle:
    """Return the verified constitution bundle for *tenant*."""

    return registry.get_bundle(tenant)


@router.post("/sign/persona-manifest", response_model=ManifestSignatureResponse, tags=["signing"])
async def sign_persona_manifest(
    payload: ManifestSigningRequest,
    signer: ManifestSigner = Depends(get_manifest_signer),
) -> ManifestSignatureResponse:
    """Sign a persona manifest payload using the service's private key."""

    canonical = json.dumps(payload.manifest, separators=(",", ":"), sort_keys=True)
    raw = canonical.encode("utf-8")
    bundle = signer.sign(raw)
    digest = hashlib.sha3_256(raw).hexdigest()
    return ManifestSignatureResponse(
        algorithm=bundle.algorithm,
        signature=bundle.signature,
        public_key=bundle.public_key,
        digest=digest,
        signed_at=datetime.utcnow(),
    )


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
