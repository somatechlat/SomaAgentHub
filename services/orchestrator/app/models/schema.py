from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # CRITICAL: Multi-tenancy support
    name = Column(Text, nullable=False)
    description = Column(Text)
    role = Column(Text)
    instructions = Column(JSONB, nullable=False)
    tools = Column(JSONB, nullable=False)
    memory_bindings = Column(JSONB)
    constraints = Column(JSONB)
    policy_scope = Column(Text)
    agent_metadata = Column(JSONB)  # Renamed from metadata (SQLAlchemy reserved name)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class CrewModel(Base):
    __tablename__ = "crews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(Text, nullable=False)
    goal = Column(Text)
    agents = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    supervisor = Column(UUID(as_uuid=True), nullable=True)
    routing_mode = Column(Text)  # 'supervisor', 'classifier', 'static'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class GraphWorkflowModel(Base):
    __tablename__ = "graph_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    definition = Column(JSONB, nullable=False)  # Stores the full GraphWorkflow JSON
    created_by = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class WorkflowInstanceModel(Base):
    __tablename__ = "workflow_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("graph_workflows.id"))
    state = Column(JSONB)
    status = Column(Text)  # RUNNING, COMPLETED, FAILED, WAITING_FOR_HUMAN
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))

class WorkflowCheckpointModel(Base):
    __tablename__ = "workflow_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"))
    node_id = Column(Text)
    state_snapshot = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class HumanReviewSessionModel(Base):
    __tablename__ = "human_review_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"))
    node_id = Column(Text)
    payload = Column(JSONB)
    status = Column(Text)  # PENDING, APPROVED, REJECTED, EXPIRED
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True))

class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    actor = Column(UUID(as_uuid=True))
    action = Column(Text)
    resource = Column(Text)
    decision = Column(Text)
    details = Column(JSONB)
