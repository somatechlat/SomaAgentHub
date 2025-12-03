from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

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
    opa_policy: Optional[str] = Field(None, alias="opaPolicy")

class AuditSpec(BaseModel):
    log_level: str = Field(default="info", alias="logLevel")
    retain_days: int = Field(default=30, alias="retainDays")

class CapsuleSpec(BaseModel):
    api_version: str = Field(default="soma/v1", alias="apiVersion")
    kind: str = Field(default="Capsule")
    metadata: Dict[str, Any]
    
    # Spec fields flattened for easier Pydantic usage, or nested if preferred.
    # Following SRS structure:
    purpose: str
    persona_id: str = Field(alias="personaId")
    tool_whitelist: List[ToolWhitelistItem] = Field(default_factory=list, alias="toolWhitelist")
    image_flavor: str = Field(default="python:3.12-slim", alias="imageFlavor")
    network_egress: List[str] = Field(default_factory=list, alias="networkEgress")
    root_permissions: bool = Field(default=False, alias="rootPermissions")
    max_runtime_seconds: int = Field(default=300, alias="maxRuntimeSeconds")
    memory_limit_mib: int = Field(default=1024, alias="memoryLimitMiB")
    cpu_limit_millicores: int = Field(default=500, alias="cpuLimitMillicores")
    env: List[EnvVar] = Field(default_factory=list)
    security: Optional[SecuritySpec] = None
    audit: Optional[AuditSpec] = None

    class Config:
        populate_by_name = True
