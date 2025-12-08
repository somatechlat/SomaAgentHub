"""
Tool Models - ToolDefinition, MCPServerDefinition, ToolInvocationRecord

SRS Section 6 - Tools & MCP Integration
Tracks tool definitions, MCP servers, and all tool invocations for observability and policy.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import (
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
class ToolType(str, Enum):
    """Tool implementation type"""

    NATIVE = "NATIVE"
    HTTP = "HTTP"
    MCP = "MCP"
    DB_QUERY = "DB_QUERY"
    SCRIPT = "SCRIPT"
    OTHER = "OTHER"


class ToolRiskLevel(str, Enum):
    """Tool risk classification"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolInvocationStatus(str, Enum):
    """Tool invocation execution status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PolicyDecision(str, Enum):
    """OPA policy decision on tool invocation"""

    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    SANITIZED = "SANITIZED"
    REQUIRES_HITL = "REQUIRES_HITL"


class AuthMethod(str, Enum):
    """MCP server authentication method"""

    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    OIDC = "OIDC"
    API_KEY = "API_KEY"
    NONE = "NONE"


# Models
class ToolDefinition(Base):
    """
    Logical tool definition (Hub-level).

    SRS Section 6.1 - ToolDefinition
    Describes tools available for agent use.
    """

    __tablename__ = "tool_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    version = Column(Text, nullable=False, default="1.0")
    type = Column(SQLEnum(ToolType), nullable=False, index=True)

    description = Column(Text, nullable=True)
    io_contract = Column(JSONB, nullable=False, default=dict)  # Input/output schema

    risk_level = Column(
        SQLEnum(ToolRiskLevel), nullable=False, default=ToolRiskLevel.LOW, index=True
    )
    default_timeout_seconds = Column(Integer, nullable=False, default=30)
    meta_data = Column("metadata", JSONB, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class MCPServerDefinition(Base):
    """
    MCP (Model Context Protocol) server definition.

    SRS Section 6.2 - MCPServerDefinition
    External tool servers providing multiple tools.
    """

    __tablename__ = "mcp_server_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    endpoint_uri = Column(Text, nullable=False)
    auth_method = Column(SQLEnum(AuthMethod), nullable=False, default=AuthMethod.NONE)
    available_tools = Column(
        JSONB, nullable=False, default=list
    )  # List of tool IDs/names

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ToolInvocationRecord(Base):
    """
    Single tool invocation record.

    SRS Section 6.3 - ToolInvocationRecord
    Tracks every tool call for observability, billing, and policy auditing.
    """

    __tablename__ = "tool_invocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    tool_definition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tool_definitions.id"),
        nullable=False,
        index=True,
    )

    # Workflow context
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_instances.id"),
        nullable=False,
        index=True,
    )
    node_execution_id = Column(
        UUID(as_uuid=True), ForeignKey("node_executions.id"), nullable=True
    )
    capsule_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_instances.id"), nullable=False
    )

    # Request/Response data (refs or inline)
    request_payload_ref = Column(Text, nullable=True)
    request_payload_inline = Column(JSONB, nullable=True)
    response_payload_ref = Column(Text, nullable=True)
    response_payload_inline = Column(JSONB, nullable=True)

    # Status
    status = Column(
        SQLEnum(ToolInvocationStatus),
        nullable=False,
        default=ToolInvocationStatus.PENDING,
        index=True,
    )

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_details = Column(JSONB, nullable=True)

    # Policy & Guardrails
    policy_decision = Column(
        SQLEnum(PolicyDecision), nullable=False, default=PolicyDecision.ALLOWED
    )
    guardrail_flags = Column(
        JSONB, nullable=False, default=list
    )  # Triggered guardrails

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )


# Pydantic models



class ToolDefinitionCreate(BaseModel):
    """API model for creating a tool definition"""

    tenant_id: PyUUID
    name: str
    version: str = "1.0"
    type: ToolType
    description: str | None = None
    io_contract: dict[str, Any] = Field(default_factory=dict)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    default_timeout_seconds: int = 30
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolDefinitionResponse(BaseModel):
    """API model for tool definition response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    version: str
    type: ToolType
    description: str | None
    io_contract: dict[str, Any]
    risk_level: ToolRiskLevel
    default_timeout_seconds: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MCPServerDefinitionCreate(BaseModel):
    """API model for creating an MCP server definition"""

    tenant_id: PyUUID
    name: str
    endpoint_uri: str
    auth_method: AuthMethod = AuthMethod.NONE
    available_tools: list[str] = Field(default_factory=list)


class MCPServerDefinitionResponse(BaseModel):
    """API model for MCP server definition response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    endpoint_uri: str
    auth_method: AuthMethod
    available_tools: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolInvocationRecordCreate(BaseModel):
    """API model for creating a tool invocation record"""

    tenant_id: PyUUID
    tool_definition_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: PyUUID | None = None
    capsule_instance_id: PyUUID
    request_payload_ref: str | None = None
    request_payload_inline: dict[str, Any] | None = None


class ToolInvocationRecordResponse(BaseModel):
    """API model for tool invocation record response"""

    id: PyUUID
    tenant_id: PyUUID
    tool_definition_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: PyUUID | None
    capsule_instance_id: PyUUID
    request_payload_ref: str | None
    request_payload_inline: dict[str, Any] | None
    response_payload_ref: str | None
    response_payload_inline: dict[str, Any] | None
    status: ToolInvocationStatus
    started_at: datetime | None
    finished_at: datetime | None
    error_details: dict[str, Any] | None
    policy_decision: PolicyDecision
    guardrail_flags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True
