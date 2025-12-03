"""
NodeExecution Model - Per-node execution tracking

SRS Section 4.7 - NodeExecution
Critical for workflow observability, replay, and RL trajectory collection.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Workflow context
    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    node_id = Column(Text, nullable=False, index=True)  # From GraphNodeDefinition
    
    # Retry tracking
    attempt = Column(Integer, nullable=False, default=1)  # Attempt number for retries
    
    # Status
    status = Column(SQLEnum(NodeExecutionStatus), nullable=False, default=NodeExecutionStatus.PENDING, index=True)
    
    # Input/Output snapshots (refs to object store or inline JSONB)
    input_snapshot_ref = Column(Text, nullable=True)  # Object store URI or "inline"
    input_snapshot_inline = Column(JSONB, nullable=True)  # Inline data if small
    output_snapshot_ref = Column(Text, nullable=True)
    output_snapshot_inline = Column(JSONB, nullable=True)
    
    # Links to specific execution types
    agent_session_binding_id = Column(UUID(as_uuid=True), ForeignKey("agent_session_bindings.id"), nullable=True)
    tool_invocation_id = Column(UUID(as_uuid=True), nullable=True)  # FK to tool_invocations (future)
    hitl_session_id = Column(UUID(as_uuid=True), ForeignKey("human_review_sessions.id"), nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_details = Column(JSONB, nullable=True)  # Structured error info
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


# Pydantic models
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID
from typing import Dict, Any


class NodeExecutionCreate(BaseModel):
    """API model for creating a node execution"""
    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_id: str
    attempt: int = 1
    input_snapshot_ref: Optional[str] = None
    input_snapshot_inline: Optional[Dict[str, Any]] = None


class NodeExecutionUpdate(BaseModel):
    """API model for updating node execution"""
    status: NodeExecutionStatus
    output_snapshot_ref: Optional[str] = None
    output_snapshot_inline: Optional[Dict[str, Any]] = None
    agent_session_binding_id: Optional[PyUUID] = None
    tool_invocation_id: Optional[PyUUID] = None
    hitl_session_id: Optional[PyUUID] = None
    error_details: Optional[Dict[str, Any]] = None


class NodeExecutionResponse(BaseModel):
    """API model for node execution response"""
    id: PyUUID
    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_id: str
    attempt: int
    status: NodeExecutionStatus
    input_snapshot_ref: Optional[str]
    input_snapshot_inline: Optional[Dict[str, Any]]
    output_snapshot_ref: Optional[str]
    output_snapshot_inline: Optional[Dict[str, Any]]
    agent_session_binding_id: Optional[PyUUID]
    tool_invocation_id: Optional[PyUUID]
    hitl_session_id: Optional[PyUUID]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    error_details: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True
