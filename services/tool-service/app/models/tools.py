"""Pydantic models for tool service APIs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AdapterMetadata(BaseModel):
    id: str
    name: str
    status: str
    version: str
    signature: str
    rate_limit_per_minute: int
    billing: Dict[str, Any] = Field(default_factory=dict)
    manifest_digest: str | None = None
    manifest: Dict[str, Any] | None = None
    source: str = "manual"
    signed_at: str | None = None


class AdapterListResponse(BaseModel):
    adapters: List[AdapterMetadata]


class AdapterExecuteRequest(BaseModel):
    action: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class AdapterExecuteResponse(BaseModel):
    job_id: str
    status: str
    duration_ms: float
    output: Dict[str, Any] = Field(default_factory=dict)
    sandbox: Dict[str, Any] = Field(default_factory=dict)
    signature: str
    rate_limit_remaining: int


class ProvisionAction(BaseModel):
    tool: str
    kind: Optional[str] = None
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProvisionRequest(BaseModel):
    tenant_id: str
    deliverable_id: str
    actions: List[ProvisionAction]
    dry_run: bool = True


class ProvisionResult(BaseModel):
    tool: str
    status: str
    job_id: str
    message: Optional[str] = None
    dry_run: bool = True


class ProvisionResponse(BaseModel):
    deliverable_id: str
    tenant_id: str
    results: List[ProvisionResult]
