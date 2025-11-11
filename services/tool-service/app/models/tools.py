"""Pydantic models for tool service APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class AdapterMetadata(BaseModel):
id: str
name: str
status: str
version: str
signature: str
rate_limit_per_minute: int
billing: dict[str, Any] = Field(default_factory=dict)
manifest_digest: str | None = None
manifest: dict[str, Any] | None = None
source: str = "manual"
signed_at: str | None = None


class AdapterListResponse(BaseModel):
adapters: list[AdapterMetadata]


class AdapterExecuteRequest(BaseModel):
action: str
arguments: dict[str, Any] = Field(default_factory=dict)


class AdapterExecuteResponse(BaseModel):
job_id: str
status: str
duration_ms: float
output: dict[str, Any] = Field(default_factory=dict)
sandbox: dict[str, Any] = Field(default_factory=dict)
signature: str
rate_limit_remaining: int


class ProvisionAction(BaseModel):
tool: str
kind: str | None = None
name: str | None = None
metadata: dict[str, Any] = Field(default_factory=dict)


class ProvisionRequest(BaseModel):
tenant_id: str
deliverable_id: str
actions: list[ProvisionAction]
dry_run: bool = True


class ProvisionResult(BaseModel):
tool: str
status: str
job_id: str
message: str | None = None
dry_run: bool = True


class ProvisionResponse(BaseModel):
deliverable_id: str
tenant_id: str
results: list[ProvisionResult]
