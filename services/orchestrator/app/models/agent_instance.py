"""AgentInstance model for Kubernetes-native agent management."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class AgentStatus(str, enum.Enum):
    """Agent lifecycle states."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class AgentInstance(SQLModel, table=True):
    """Database model for tracking agent instances in Kubernetes."""
    
    __tablename__ = "agent_instances"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )
    
    agent_type: str = Field(
        max_length=100,
        description="Type of agent (code_generator, ui_customizer, etc.)"
    )
    
    capsule_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="capsules.capsule_id",
        description="Associated capsule ID"
    )
    
    tenant_id: uuid.UUID = Field(
        index=True,
        description="Tenant identifier"
    )
    
    user_id: uuid.UUID = Field(
        index=True,
        description="User who initiated the agent"
    )
    
    status: AgentStatus = Field(
        default=AgentStatus.PENDING,
        index=True,
        description="Current agent state"
    )
    
    k8s_namespace: str = Field(
        max_length=100,
        description="Kubernetes namespace"
    )
    
    k8s_job_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Kubernetes job name (for batch agents)"
    )
    
    k8s_deployment_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Kubernetes deployment name (for long-running agents)"
    )
    
    # Avoid using attribute name `metadata` which is reserved by SQLAlchemy.
    meta: dict = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB),
        description="Additional Kubernetes metadata",
    )
    
    resource_requests: dict = Field(
        default_factory=dict,
        sa_column=Column("resource_requests", JSONB),
        description="CPU/memory resource requests",
    )

    resource_limits: dict = Field(
        default_factory=dict,
        sa_column=Column("resource_limits", JSONB),
        description="CPU/memory resource limits",
    )
    
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))

    updated_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()))
    
    started_at: Optional[datetime] = Field(
        default=None,
        description="When the agent started running"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the agent completed"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if agent failed"
    )
    
    # Keep default SQLModel behavior; explicit Config not required here.