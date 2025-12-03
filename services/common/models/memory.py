"""
Memory Integration Models - MemoryBindingSpec, MemoryOperationRecord

SRS Section 7 - Memory Integration with SomaBrain
Tracks memory bindings and all memory operations for observability and RL.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# Enums
class MemoryOperationType(str, Enum):
    """Type of memory operation"""
    READ = "READ"
    WRITE = "WRITE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# Models
class MemoryBindingSpec(Base):
    """
    Memory binding specification for workflows.
    
    SRS Section 7.1 - MemoryBindingSpec
    Describes how workflows connect to SomaBrain memory systems.
    """
    __tablename__ = "memory_binding_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Context
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True)
    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    
    # SomaBrain references
    somabrain_memory_bank_refs = Column(JSONB, nullable=False, default=list)  # List of ExternalRef IDs
    somabrain_example_store_ref_id = Column(UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=True)
    
    # Scoping
    scopes = Column(JSONB, nullable=False, default=dict)  # global, per-role, per-node configs
    
    # Policies
    write_policy = Column(JSONB, nullable=False, default=dict)  # What gets persisted (RAW, SUMMARIZED, ANONYMIZED)
    read_policy = Column(JSONB, nullable=False, default=dict)  # Which types of memories allowed
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class MemoryOperationRecord(Base):
    """
    Record of a single memory operation.
    
    SRS Section 7.2 - MemoryOperationRecord
    Logs each memory interaction for observability and RL training.
    """
    __tablename__ = "memory_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Workflow context
    workflow_instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    node_execution_id = Column(UUID(as_uuid=True), ForeignKey("node_executions.id"), nullable=True)
    
    # Operation details
    operation_type = Column(SQLEnum(MemoryOperationType), nullable=False, index=True)
    somabrain_ref_id = Column(UUID(as_uuid=True), ForeignKey("external_refs.id"), nullable=False)  # MemoryBank or ExampleStore
    
    # Summaries (avoid storing full memory content)
    request_summary = Column(JSONB, nullable=True)
    response_summary = Column(JSONB, nullable=True)
    
    # Policy decision
    policy_decision = Column(Text, nullable=True)  # ALLOWED, DENIED, SANITIZED
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


# Pydantic models
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID
from typing import List, Dict, Any


class MemoryBindingSpecCreate(BaseModel):
    """API model for creating a memory binding spec"""
    tenant_id: PyUUID
    task_id: Optional[PyUUID] = None
    workflow_instance_id: PyUUID
    somabrain_memory_bank_refs: List[PyUUID] = Field(default_factory=list)
    somabrain_example_store_ref_id: Optional[PyUUID] = None
    scopes: Dict[str, Any] = Field(default_factory=dict)
    write_policy: Dict[str, Any] = Field(default_factory=dict)
    read_policy: Dict[str, Any] = Field(default_factory=dict)


class MemoryBindingSpecResponse(BaseModel):
    """API model for memory binding spec response"""
    id: PyUUID
    tenant_id: PyUUID
    task_id: Optional[PyUUID]
    workflow_instance_id: PyUUID
    somabrain_memory_bank_refs: List[PyUUID]
    somabrain_example_store_ref_id: Optional[PyUUID]
    scopes: Dict[str, Any]
    write_policy: Dict[str, Any]
    read_policy: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MemoryOperationRecordCreate(BaseModel):
    """API model for creating a memory operation record"""
    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: Optional[PyUUID] = None
    operation_type: MemoryOperationType
    somabrain_ref_id: PyUUID
    request_summary: Optional[Dict[str, Any]] = None
    response_summary: Optional[Dict[str, Any]] = None
    policy_decision: Optional[str] = None


class MemoryOperationRecordResponse(BaseModel):
    """API model for memory operation record response"""
    id: PyUUID
    tenant_id: PyUUID
    workflow_instance_id: PyUUID
    node_execution_id: Optional[PyUUID]
    operation_type: MemoryOperationType
    somabrain_ref_id: PyUUID
    request_summary: Optional[Dict[str, Any]]
    response_summary: Optional[Dict[str, Any]]
    policy_decision: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
