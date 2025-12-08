from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolWhitelistItem(BaseModel):
    name: str
    version: str


class EnvVar(BaseModel):
    name: str
    value: str


class SecuritySpec(BaseModel):
    opa_policy: str | None = Field(None, alias="opaPolicy")


class AuditSpec(BaseModel):
    log_level: str = Field(default="info", alias="logLevel")
    retain_days: int = Field(default=30, alias="retainDays")


class CapsuleSpec(BaseModel):
    api_version: str = Field(default="soma/v1", alias="apiVersion")
    kind: str = Field(default="Capsule")
    metadata: dict[str, Any]

    # Spec fields flattened for easier Pydantic usage, or nested if preferred.
    # Following SRS structure:
    purpose: str
    persona_id: str = Field(alias="personaId")
    tool_whitelist: list[ToolWhitelistItem] = Field(
        default_factory=list, alias="toolWhitelist"
    )
    image_flavor: str = Field(default="python:3.12-slim", alias="imageFlavor")
    network_egress: list[str] = Field(default_factory=list, alias="networkEgress")
    root_permissions: bool = Field(default=False, alias="rootPermissions")
    max_runtime_seconds: int = Field(default=300, alias="maxRuntimeSeconds")
    memory_limit_mib: int = Field(default=1024, alias="memoryLimitMiB")
    cpu_limit_millicores: int = Field(default=500, alias="cpuLimitMillicores")
    env: list[EnvVar] = Field(default_factory=list)
    security: SecuritySpec | None = None
    audit: AuditSpec | None = None

    class Config:
        populate_by_name = True
