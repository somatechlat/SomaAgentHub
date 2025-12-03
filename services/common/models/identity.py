"""
Identity Models - TenantRef, PrincipalRef, ExternalRef

These models provide cross-cutting identity and reference management for SomaAgentHub.
All models implement multi-tenancy and external system integration per SRS Section 1.
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
class TenantStatus(str, Enum):
    """Tenant lifecycle status"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class PrincipalType(str, Enum):
    """Type of principal (actor)"""
    USER = "USER"
    SERVICE = "SERVICE"
    SYSTEM = "SYSTEM"


class ExternalSystem(str, Enum):
    """External systems that Hub integrates with"""
    SOMA_AGENT01 = "SOMA_AGENT01"
    SOMABRAIN = "SOMABRAIN"
    GIT = "GIT"
    OBJECT_STORE = "OBJECT_STORE"
    EXTERNAL_RUNTIMES = "EXTERNAL_RUNTIMES"
    OTHER = "OTHER"


# Models
class TenantRef(Base):
    """
    Tenant reference model - represents a logical tenant (organization/workspace).
    
    SRS Section 1.1
    All other models MUST have a tenant_id FK to this table.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)  # Human-readable tenant name
    status = Column(SQLEnum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PrincipalRef(Base):
    """
    Principal reference model - represents actors (users, services, system).
    
    SRS Section 1.2
    Used for authentication, authorization, and audit logging.
    """
    __tablename__ = "principals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    principal_type = Column(SQLEnum(PrincipalType), nullable=False, index=True)
    principal_id = Column(Text, nullable=False)  # ID from identity provider (e.g., Keycloak subject)
    display_name = Column(Text, nullable=False)
    roles = Column(JSONB, nullable=False, default=list)  # List of role strings
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for fast principal lookup
    __table_args__ = (
        {'schema': None}  # Use default schema
    )


class ExternalRef(Base):
    """
    External reference model - generic model for referencing objects in other systems.
    
    SRS Section 1.3
    Used to link Hub objects to:
    - SomaAgent01 agents and sessions
    - SomaBrain personas, memory banks, example stores
    - Git repositories
    - Object store buckets
    - External runtimes
    """
    __tablename__ = "external_refs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    system = Column(SQLEnum(ExternalSystem), nullable=False, index=True)
    type = Column(Text, nullable=False)  # e.g., "AGENT", "SESSION", "PERSONA", "MEMORY_BANK"
    external_id = Column(Text, nullable=False)  # ID in the external system
    uri = Column(Text, nullable=True)  # Optional structured URI
    metadata = Column(JSONB, nullable=False, default=dict)  # System-specific metadata
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Composite index for fast external lookups
    __table_args__ = (
        {'schema': None}
    )


# Pydantic models for API validation
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID


class TenantRefCreate(BaseModel):
    """API model for creating a tenant"""
    name: str = Field(..., min_length=1, max_length=255)


class TenantRefResponse(BaseModel):
    """API model for tenant response"""
    id: PyUUID
    name: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PrincipalRefCreate(BaseModel):
    """API model for creating a principal"""
    tenant_id: PyUUID
    principal_type: PrincipalType
    principal_id: str
    display_name: str
    roles: list[str] = Field(default_factory=list)


class PrincipalRefResponse(BaseModel):
    """API model for principal response"""
    id: PyUUID
    tenant_id: PyUUID
    principal_type: PrincipalType
    principal_id: str
    display_name: str
    roles: list[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExternalRefCreate(BaseModel):
    """API model for creating an external reference"""
    tenant_id: PyUUID
    system: ExternalSystem
    type: str
    external_id: str
    uri: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ExternalRefResponse(BaseModel):
    """API model for external reference response"""
    id: PyUUID
    tenant_id: PyUUID
    system: ExternalSystem
    type: str
    external_id: str
    uri: Optional[str]
    metadata: dict
    created_at: datetime
    
    class Config:
        from_attributes = True
