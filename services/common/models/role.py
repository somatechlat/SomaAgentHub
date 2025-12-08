"""
Role and Agent Binding Models

Implements role-based agent architecture per SRS Section 5.
Separates logical roles from Agent01 implementations for flexibility and RL training.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import Base


# Enums
class AgentSessionStatus(str, Enum):
    """Agent session status"""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


# Models
class RoleDefinition(Base):
    """
    Logical role definition for reasoning pipelines.

    SRS Section 5.1 - RoleDefinition
    Examples: PLANNER, SOLVER, VERIFIER, CORRECTOR, JUDGE, DEFENDER, ATTACKER
    """

    __tablename__ = "role_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)  # e.g., "PLANNER", "SOLVER"
    description = Column(Text, nullable=True)

    # Default persona from SomaBrain
    default_persona_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=True
    )

    expected_behavior = Column(
        Text, nullable=True
    )  # Documentation on how to use this role

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Unique constraint: name per tenant
    __table_args__ = {"schema": None}


class AgentBinding(Base):
    """
    Binding between a logical role and an Agent01 agent implementation.

    SRS Section 5.2 - AgentBinding
    Maps Hub roles to actual agents in SomaAgent01.
    """

    __tablename__ = "agent_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("role_definitions.id"),
        nullable=False,
        index=True,
    )

    # Reference to Agent01 agent (external system)
    agent01_agent_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=False
    )

    # Capability metadata
    supported_task_types = Column(
        JSONB, nullable=False, default=list
    )  # e.g., ["APP_BUILD", "RESEARCH"]
    supported_domains = Column(
        JSONB, nullable=False, default=list
    )  # e.g., ["tourism", "healthcare"]

    # Default Capsule for this binding
    default_capsule_definition_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_definitions.id"), nullable=True
    )

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AgentSessionBinding(Base):
    """
    Runtime binding for an Agent01 session used in a workflow node.

    SRS Section 5.3 - AgentSessionBinding
    Tracks actual agent sessions during workflow execution.
    """

    __tablename__ = "agent_session_bindings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Link to agent binding
    agent_binding_id = Column(
        UUID(as_uuid=True), ForeignKey("agent_bindings.id"), nullable=False, index=True
    )

    # Link to workflow execution
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_instances.id"),
        nullable=False,
        index=True,
    )
    node_execution_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # FK to node_executions (future)

    # Capsule for this session
    capsule_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_instances.id"), nullable=False
    )

    # SomaBrain references for this session
    somabrain_persona_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=True
    )
    somabrain_memory_bank_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=True
    )

    # Agent01 session reference
    agent01_session_ref_id = Column(
        UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=False
    )

    # Lifecycle
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    closed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SQLEnum(AgentSessionStatus),
        nullable=False,
        default=AgentSessionStatus.OPEN,
        index=True,
    )


# Pydantic models for API



class RoleDefinitionCreate(BaseModel):
    """API model for creating a role definition"""

    tenant_id: PyUUID
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    default_persona_ref_id: PyUUID | None = None
    expected_behavior: str | None = None


class RoleDefinitionResponse(BaseModel):
    """API model for role definition response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    description: str | None
    default_persona_ref_id: PyUUID | None
    expected_behavior: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentBindingCreate(BaseModel):
    """API model for creating an agent binding"""

    tenant_id: PyUUID
    role_id: PyUUID
    agent01_agent_ref_id: PyUUID
    supported_task_types: list[str] = Field(default_factory=list)
    supported_domains: list[str] = Field(default_factory=list)
    default_capsule_definition_id: PyUUID | None = None


class AgentBindingResponse(BaseModel):
    """API model for agent binding response"""

    id: PyUUID
    tenant_id: PyUUID
    role_id: PyUUID
    agent01_agent_ref_id: PyUUID
    supported_task_types: list[str]
    supported_domains: list[str]
    default_capsule_definition_id: PyUUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentSessionBindingCreate(BaseModel):
    """API model for creating an agent session binding"""

    tenant_id: PyUUID
    agent_binding_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: PyUUID | None = None
    capsule_instance_id: PyUUID
    somabrain_persona_ref_id: PyUUID | None = None
    somabrain_memory_bank_ref_id: PyUUID | None = None
    agent01_session_ref_id: PyUUID


class AgentSessionBindingResponse(BaseModel):
    """API model for agent session binding response"""

    id: PyUUID
    tenant_id: PyUUID
    agent_binding_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: PyUUID | None
    capsule_instance_id: PyUUID
    somabrain_persona_ref_id: PyUUID | None
    somabrain_memory_bank_ref_id: PyUUID | None
    agent01_session_ref_id: PyUUID
    created_at: datetime
    closed_at: datetime | None
    status: AgentSessionStatus

    class Config:
        from_attributes = True
