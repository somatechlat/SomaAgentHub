"""
Capsule Models - CapsuleDefinition and CapsuleInstance

Complete Capsule system per SRS Section 2.
Capsules are universal contracts across Hub, Agent01, Brain, RL/export, and policy.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import Base


# Enums
class CapsuleStatus(str, Enum):
    """Capsule definition lifecycle status"""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class EgressMode(str, Enum):
    """Network egress control mode"""

    DENY_ALL = "DENY_ALL"
    ALLOW_LIST = "ALLOW_LIST"
    ALLOW_ALL_WITH_MONITORING = "ALLOW_ALL_WITH_MONITORING"


class HITLMode(str, Enum):
    """Human-in-the-loop mode"""

    NEVER = "NEVER"
    ON_HIGH_RISK = "ON_HIGH_RISK"
    ALWAYS_ON_CRITICAL_NODES = "ALWAYS_ON_CRITICAL_NODES"


class RLExportScope(str, Enum):
    """RL export data scope"""

    ANONYMIZED_ONLY = "ANONYMIZED_ONLY"
    PSEUDONYMIZED = "PSEUDONYMIZED"
    FULL = "FULL"


class DataClassification(str, Enum):
    """Data classification levels"""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"


class CapsuleScope(str, Enum):
    """Capsule instance scope"""

    TASK = "TASK"
    WORKFLOW = "WORKFLOW"
    NODE = "NODE"
    ROLE = "ROLE"


class AllowedRuntime(str, Enum):
    """Allowed runtime environments"""

    SOMA_STACK_ONLY = "SOMA_STACK_ONLY"
    SOMA_STACK_PLUS_EXTERNAL = "SOMA_STACK_PLUS_EXTERNAL"


# Models
class CapsuleDefinition(Base):
    """
    Capsule Definition - Template/blueprint for Capsules.

    SRS Section 2.1 - Complete implementation with all fields.
    Immutable once ACTIVE - create new version for changes.
    """

    __tablename__ = "capsule_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Basic metadata
    name = Column(Text, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(
        SQLEnum(CapsuleStatus), nullable=False, default=CapsuleStatus.DRAFT, index=True
    )
    description = Column(Text, nullable=True)

    # Persona Section
    default_persona_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=True
    )
    role_overrides = Column(
        JSONB, nullable=False, default=dict
    )  # role_id -> persona_ref_id

    # Tool Policy Section
    allowed_tools = Column(
        JSONB, nullable=False, default=list
    )  # List of tool identifiers
    prohibited_tools = Column(JSONB, nullable=False, default=list)
    allowed_mcp_servers = Column(
        JSONB, nullable=False, default=list
    )  # List of MCP server identifiers
    tool_risk_profile = Column(
        JSONB, nullable=False, default=dict
    )  # tool_id -> risk_level

    # Runtime Section
    max_wall_clock_seconds = Column(Integer, nullable=False, default=300)
    max_concurrent_nodes = Column(Integer, nullable=True)
    allowed_runtimes = Column(
        JSONB, nullable=False, default=list
    )  # List of AllowedRuntime
    resource_profile = Column(JSONB, nullable=False, default=dict)  # CPU/memory hints

    # Network/Egress Section
    allowed_domains = Column(JSONB, nullable=False, default=list)
    blocked_domains = Column(JSONB, nullable=False, default=list)
    egress_mode = Column(
        SQLEnum(EgressMode), nullable=False, default=EgressMode.ALLOW_LIST
    )

    # Policy Section
    opa_policy_packages = Column(
        JSONB, nullable=False, default=list
    )  # List of OPA package IDs
    guardrail_profiles = Column(
        JSONB, nullable=False, default=list
    )  # List of guardrail configs

    # HITL Section
    default_hitl_mode = Column(
        SQLEnum(HITLMode), nullable=False, default=HITLMode.ON_HIGH_RISK
    )
    risk_thresholds = Column(
        JSONB, nullable=False, default=dict
    )  # risk_level -> HITL requirement
    max_pending_hitl = Column(Integer, nullable=True)

    # RL / Data Reuse Section
    rl_export_allowed = Column(Boolean, nullable=False, default=False)
    rl_export_scope = Column(
        SQLEnum(RLExportScope), nullable=False, default=RLExportScope.ANONYMIZED_ONLY
    )
    rl_excluded_fields = Column(
        JSONB, nullable=False, default=list
    )  # Field paths to exclude
    example_store_policy = Column(
        JSONB, nullable=False, default=dict
    )  # Constraints for examples

    # Compliance Section
    data_classification = Column(
        SQLEnum(DataClassification), nullable=False, default=DataClassification.INTERNAL
    )
    retention_policy_days = Column(Integer, nullable=False, default=30)

    # Lifecycle
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Unique constraint: name + version per tenant
    __table_args__ = {"schema": None}


class CapsuleInstance(Base):
    """
    Capsule Instance - Concrete Capsule bound to a task/workflow/node/role.

    SRS Section 2.2
    Runtime binding with resolved configuration and override chains.
    """

    __tablename__ = "capsule_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Link to definition
    capsule_definition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("capsule_definitions.id"),
        nullable=False,
        index=True,
    )
    capsule_definition_version = Column(Integer, nullable=False)

    # Scope binding
    scope = Column(SQLEnum(CapsuleScope), nullable=False, index=True)
    scope_reference = Column(
        Text, nullable=False
    )  # Task ID, Workflow ID, Node ID, or Role name

    # Lifecycle
    start_time = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Resolved configuration snapshot (immutable after creation)
    effective_config = Column(JSONB, nullable=False)  # Fully resolved config

    # Override chain (for hierarchical Capsules)
    derived_from_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_instances.id"), nullable=True
    )

    # Lifecycle
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )


# Pydantic models for API



class CapsuleDefinitionCreate(BaseModel):
    """API model for creating a Capsule definition"""

    tenant_id: PyUUID
    name: str
    version: int = 1
    description: str | None = None

    # Persona
    default_persona_ref_id: PyUUID | None = None
    role_overrides: dict[str, PyUUID] = Field(default_factory=dict)

    # Tools
    allowed_tools: list[str] = Field(default_factory=list)
    prohibited_tools: list[str] = Field(default_factory=list)
    allowed_mcp_servers: list[str] = Field(default_factory=list)
    tool_risk_profile: dict[str, str] = Field(default_factory=dict)

    # Runtime
    max_wall_clock_seconds: int = 300
    max_concurrent_nodes: int | None = None
    allowed_runtimes: list[str] = Field(default_factory=lambda: ["SOMA_STACK_ONLY"])
    resource_profile: dict[str, Any] = Field(default_factory=dict)

    # Network
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    egress_mode: EgressMode = EgressMode.ALLOW_LIST

    # Policy
    opa_policy_packages: list[str] = Field(default_factory=list)
    guardrail_profiles: list[str] = Field(default_factory=list)

    # HITL
    default_hitl_mode: HITLMode = HITLMode.ON_HIGH_RISK
    risk_thresholds: dict[str, str] = Field(default_factory=dict)
    max_pending_hitl: int | None = None

    # RL
    rl_export_allowed: bool = False
    rl_export_scope: RLExportScope = RLExportScope.ANONYMIZED_ONLY
    rl_excluded_fields: list[str] = Field(default_factory=list)
    example_store_policy: dict[str, Any] = Field(default_factory=dict)

    # Compliance
    data_classification: DataClassification = DataClassification.INTERNAL
    retention_policy_days: int = 30


class CapsuleDefinitionResponse(BaseModel):
    """API model for Capsule definition response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    version: int
    status: CapsuleStatus
    description: str | None

    # All fields from definition
    default_persona_ref_id: PyUUID | None
    role_overrides: dict[str, PyUUID]
    allowed_tools: list[str]
    prohibited_tools: list[str]
    allowed_mcp_servers: list[str]
    tool_risk_profile: dict[str, str]
    max_wall_clock_seconds: int
    max_concurrent_nodes: int | None
    allowed_runtimes: list[str]
    resource_profile: dict[str, Any]
    allowed_domains: list[str]
    blocked_domains: list[str]
    egress_mode: EgressMode
    opa_policy_packages: list[str]
    guardrail_profiles: list[str]
    default_hitl_mode: HITLMode
    risk_thresholds: dict[str, str]
    max_pending_hitl: int | None
    rl_export_allowed: bool
    rl_export_scope: RLExportScope
    rl_excluded_fields: list[str]
    example_store_policy: dict[str, Any]
    data_classification: DataClassification
    retention_policy_days: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CapsuleInstanceCreate(BaseModel):
    """API model for creating a Capsule instance"""

    tenant_id: PyUUID
    capsule_definition_id: PyUUID
    capsule_definition_version: int
    scope: CapsuleScope
    scope_reference: str
    effective_config: dict[str, Any]
    derived_from_id: PyUUID | None = None


class CapsuleInstanceResponse(BaseModel):
    """API model for Capsule instance response"""

    id: PyUUID
    tenant_id: PyUUID
    capsule_definition_id: PyUUID
    capsule_definition_version: int
    scope: CapsuleScope
    scope_reference: str
    start_time: datetime
    end_time: datetime | None
    effective_config: dict[str, Any]
    derived_from_id: PyUUID | None
    created_at: datetime

    class Config:
        from_attributes = True
