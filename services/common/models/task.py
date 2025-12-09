"""
Task Models - TaskRecord and TaskStatusHistory

Top-level orchestration entities that coordinate blueprints, plans, and workflows.
SRS Section 4.1, 4.2
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


class TaskStatus(str, Enum):
    """Task lifecycle status - SRS Section 4.1"""

    RECEIVED = "RECEIVED"
    ANALYZING = "ANALYZING"
    DELEGATED_TO_HUB = "DELEGATED_TO_HUB"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_ON_HITL = "WAITING_ON_HITL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskRecord(Base):
    """
    Top-level task tracking model.

    SRS Section 4.1 - TaskRecord
    Represents a user's big request that may span multiple workflows.
    Links to blueprints, plans, and workflow instances.
    """

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # User and source tracking
    user_principal_id = Column(
        UUID(as_uuid=True), ForeignKey("principals.id"), nullable=False
    )
    source_application = Column(Text, nullable=False)  # e.g., "SOMA_AGENT_APP"
    original_request_text = Column(Text, nullable=False)

    # Task classification
    task_type = Column(
        Text, nullable=False, index=True
    )  # e.g., "APP_BUILD", "RESEARCH_PROJECT"
    domain = Column(Text, nullable=True)  # e.g., "tourism", "healthcare"
    priority = Column(
        SQLEnum(TaskPriority), nullable=False, default=TaskPriority.NORMAL
    )
    sla = Column(JSONB, nullable=True)  # SLA expectations (response time windows)

    # Current status
    status = Column(
        SQLEnum(TaskStatus), nullable=False, default=TaskStatus.RECEIVED, index=True
    )

    # Links to downstream entities
    plan_spec_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # FK to plan_specs (future)
    root_workflow_instance_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # FK to workflow_instances
    capsule_instance_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # FK to capsule_instances (future)

    # Lifecycle timestamps
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    labels = Column(
        JSONB, nullable=False, default=dict
    )  # Flexible tags (experiments, versions, etc.)
    error_summary = Column(JSONB, nullable=True)  # Structured error info if FAILED


class TaskStatusHistory(Base):
    """
    Audit trail for task status changes.

    SRS Section 4.2 - TaskStatusHistory
    Auto-populated on every status transition.
    """

    __tablename__ = "task_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )

    previous_status = Column(SQLEnum(TaskStatus), nullable=True)  # NULL for first entry
    new_status = Column(SQLEnum(TaskStatus), nullable=False)

    timestamp = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    reason = Column(Text, nullable=True)  # Optional explanation for transition
    actor_principal_id = Column(
        UUID(as_uuid=True), ForeignKey("principals.id"), nullable=True
    )


# Pydantic models for API


class TaskRecordCreate(BaseModel):
    """API model for creating a task"""

    tenant_id: PyUUID
    user_principal_id: PyUUID
    source_application: str
    original_request_text: str
    task_type: str
    domain: str | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    sla: dict | None = None
    labels: dict = Field(default_factory=dict)


class TaskRecordUpdate(BaseModel):
    """API model for updating task status"""

    status: TaskStatus
    reason: str | None = None
    actor_principal_id: PyUUID | None = None


class TaskRecordResponse(BaseModel):
    """API model for task response"""

    id: PyUUID
    tenant_id: PyUUID
    user_principal_id: PyUUID
    source_application: str
    original_request_text: str
    task_type: str
    domain: str | None
    priority: TaskPriority
    sla: dict | None
    status: TaskStatus
    plan_spec_id: PyUUID | None
    root_workflow_instance_id: PyUUID | None
    capsule_instance_id: PyUUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    labels: dict
    error_summary: dict | None

    class Config:
        from_attributes = True


class TaskStatusHistoryResponse(BaseModel):
    """API model for task status history"""

    id: PyUUID
    task_id: PyUUID
    previous_status: TaskStatus | None
    new_status: TaskStatus
    timestamp: datetime
    reason: str | None
    actor_principal_id: PyUUID | None

    class Config:
        from_attributes = True
