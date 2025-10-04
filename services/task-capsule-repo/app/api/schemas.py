"""Pydantic schemas for capsule marketplace operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class CapsuleSummary(BaseModel):
    id: int = Field(..., description="Internal submission identifier")
    capsule_id: str
    version: str
    owner: str
    status: Literal["pending", "approved", "rejected"]
    summary: str | None = None
    submitted_at: datetime = Field(..., alias="created_at")
    reviewer: str | None = None
    approved_at: datetime | None = None


class CapsuleSubmissionRequest(BaseModel):
    capsule_id: str = Field(..., description="Unique capsule slug (e.g., plane_project_starter)")
    version: str = Field(..., description="Semantic version of the capsule package")
    owner: str = Field(..., description="Submitting tenant or partner identifier")
    summary: str | None = Field(None, description="Short human readable description")
    definition: Dict[str, Any] = Field(..., description="Capsule manifest payload")
    attestation_hash: str = Field(..., description="SHA-256 hash of the manifest payload")
    attestation_signature: str | None = Field(
        None,
        description="Signature from the submitter proving integrity (optional during dev).",
    )
    compliance_report: Dict[str, Any] | None = Field(
        None,
        description="Optional automated lint/compliance findings.",
    )
    tenant_scope: str = Field(
        "global",
        description="Scope for marketplace visibility (global or specific tenant)",
    )


class CapsuleSubmissionResponse(BaseModel):
    id: int
    capsule_id: str
    version: str
    status: Literal["pending", "approved", "rejected"]
    attestation_hash: str
    reviewer: str | None = None


class CapsuleSubmissionListResponse(BaseModel):
    submissions: list[CapsuleSummary]


class CapsuleReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reviewer: str
    notes: str | None = None
    is_override: bool = Field(
        False,
        description="Flag true when bypassing automated checks or re-approving",
    )


class CapsuleReviewResponse(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected"]
    reviewer: str | None
    approved_at: datetime | None = None
    rejected_reason: str | None = None


class CapsuleCatalogEntry(BaseModel):
    id: str
    version: str
    summary: str | None = None
    type: str = "capsule"
    source: Literal["filesystem", "marketplace"] = "filesystem"


class CapsuleDetail(BaseModel):
    capsule: Dict[str, Any]
    status: Literal["filesystem", "pending", "approved", "rejected"]
    submission_id: int | None = None
    compliance_report: Dict[str, Any] | None = None


class CapsuleInstallRequest(BaseModel):
    capsule_id: str
    version: str | None = None
    tenant_id: str
    environment: str = Field("prod", description="Installation environment (prod, staging, etc.)")
    installed_by: str
    notes: str | None = None


class CapsuleInstallResponse(BaseModel):
    installation_id: int
    package_id: int
    capsule_id: str
    version: str
    tenant_id: str
    environment: str
    status: str
    installed_at: datetime
    installed_by: str
    notes: str | None = None


class CapsuleInstallationListResponse(BaseModel):
    installations: list[CapsuleInstallResponse]


class CapsuleRollbackRequest(BaseModel):
    notes: str | None = None
    performed_by: str
