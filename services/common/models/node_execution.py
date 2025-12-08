"""
NodeExecution Model - Per-node execution tracking

SRS Section 4.7 - NodeExecution
Critical for workflow observability, replay, and RL trajectory collection.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from pydantic import BaseModel
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


class NodeExecutionStatus(str, Enum):
    """Node execution status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class NodeExecution(Base):
    """
    Single execution of a node in a workflow instance.

    SRS Section 4.7 - NodeExecution
    Enables per-node observability, retry tracking, and RL data collection.
    """

    __tablename__ = "node_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Workflow context
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_instances.id"),
        nullable=False,
        index=True,
    )
    node_id = Column(Text, nullable=False, index=True)  # From GraphNodeDefinition

    # Retry tracking
    attempt = Column(Integer, nullable=False, default=1)  # Attempt number for retries

    # Status
    status = Column(
        SQLEnum(NodeExecutionStatus),
        nullable=False,
        default=NodeExecutionStatus.PENDING,
        index=True,
    )

    # Input/Output snapshots (refs to object store or inline JSONB)
    input_snapshot_ref = Column(Text, nullable=True)  # Object store URI or "inline"
    input_snapshot_inline = Column(JSONB, nullable=True)  # Inline data if small
    output_snapshot_ref = Column(Text, nullable=True)
    output_snapshot_inline = Column(JSONB, nullable=True)

    # Links to specific execution types
    agent_session_binding_id = Column(
        UUID(as_uuid=True), ForeignKey("agent_session_bindings.id"), nullable=True
    )
    tool_invocation_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # FK to tool_invocations (future)
    hitl_session_id = Column(
        UUID(as_uuid=True), ForeignKey("human_review_sessions.id"), nullable=True
    )

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_details = Column(JSONB, nullable=True)  # Structured error info

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


# Pydantic models



class NodeExecutionCreate(BaseModel):
    """API model for creating a node execution"""

    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_id: str
    attempt: int = 1
    input_snapshot_ref: str | None = None
    input_snapshot_inline: dict[str, Any] | None = None


class NodeExecutionUpdate(BaseModel):
    """API model for updating node execution"""

    status: NodeExecutionStatus
    output_snapshot_ref: str | None = None
    output_snapshot_inline: dict[str, Any] | None = None
    agent_session_binding_id: PyUUID | None = None
    tool_invocation_id: PyUUID | None = None
    hitl_session_id: PyUUID | None = None
    error_details: dict[str, Any] | None = None


class NodeExecutionResponse(BaseModel):
    """API model for node execution response"""

    id: PyUUID
    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_id: str
    attempt: int
    status: NodeExecutionStatus
    input_snapshot_ref: str | None
    input_snapshot_inline: dict[str, Any] | None
    output_snapshot_ref: str | None
    output_snapshot_inline: dict[str, Any] | None
    agent_session_binding_id: PyUUID | None
    tool_invocation_id: PyUUID | None
    hitl_session_id: PyUUID | None
    started_at: datetime | None
    ended_at: datetime | None
    error_details: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True
