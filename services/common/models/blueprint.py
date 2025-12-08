"""
Blueprint and Planning Models - BlueprintDefinition, PlanSpec

SRS Section 3 - Blueprint & Planning System
Reusable orchestration patterns with parameterization and validation.
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
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# Enums
class BlueprintStatus(str, Enum):
    """Blueprint lifecycle status"""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class WizardMode(str, Enum):
    """Wizard UI requirement"""

    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    DISABLED = "DISABLED"


# Models
class BlueprintDefinition(Base):
    """
    Reusable orchestration pattern blueprint.

    SRS Section 3.1 - BlueprintDefinition
    Templates for common workflow patterns (e.g., "tourism-app-blueprint").
    """

    __tablename__ = "blueprint_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(
        SQLEnum(BlueprintStatus),
        nullable=False,
        default=BlueprintStatus.DRAFT,
        index=True,
    )
    description = Column(Text, nullable=True)

    # Supported task types
    supported_task_types = Column(
        JSONB, nullable=False, default=list
    )  # e.g., ["APP_BUILD", "SERVICE_BUILD"]

    # Parameters
    required_parameters = Column(
        JSONB, nullable=False, default=list
    )  # List of BlueprintParameterDefinition
    optional_parameters = Column(JSONB, nullable=False, default=list)

    # Default Capsule
    default_capsule_definition_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_definitions.id"), nullable=True
    )

    # Graph template
    graph_template_ref = Column(
        Text, nullable=True
    )  # Reference to template or generator

    # UI configuration
    wizard_mode = Column(
        SQLEnum(WizardMode), nullable=False, default=WizardMode.OPTIONAL
    )
    constraints = Column(JSONB, nullable=False, default=dict)  # Additional constraints

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PlanSpec(Base):
    """
    Concrete plan for a specific task from a blueprint.

    SRS Section 3.3 - PlanSpec
    Blueprint + user parameters → validated plan.
    """

    __tablename__ = "plan_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Link to task and blueprint
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True
    )
    blueprint_definition_id = Column(
        UUID(as_uuid=True), ForeignKey("blueprint_definitions.id"), nullable=False
    )
    blueprint_version = Column(Integer, nullable=False)

    # Validated parameters
    parameters = Column(JSONB, nullable=False)  # Key/value map of validated parameters

    # Resolved artifacts
    capsule_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_instances.id"), nullable=False
    )
    graph_workflow_definition_id = Column(
        UUID(as_uuid=True), ForeignKey("graph_workflows.id"), nullable=False
    )

    # Reasoning pipelines applied
    reasoning_pipelines = Column(
        JSONB, nullable=False, default=list
    )  # Refs to ReasoningPipelineSpecs

    # Creator
    created_by_principal_id = Column(
        UUID(as_uuid=True), ForeignKey("principals.id"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


# Pydantic models



class BlueprintDefinitionCreate(BaseModel):
    """API model for creating a blueprint definition"""

    tenant_id: PyUUID
    name: str
    version: int = 1
    description: str | None = None
    supported_task_types: list[str] = Field(default_factory=list)
    required_parameters: list[dict[str, Any]] = Field(default_factory=list)
    optional_parameters: list[dict[str, Any]] = Field(default_factory=list)
    default_capsule_definition_id: PyUUID | None = None
    graph_template_ref: str | None = None
    wizard_mode: WizardMode = WizardMode.OPTIONAL
    constraints: dict[str, Any] = Field(default_factory=dict)


class BlueprintDefinitionResponse(BaseModel):
    """API model for blueprint definition response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    version: int
    status: BlueprintStatus
    description: str | None
    supported_task_types: list[str]
    required_parameters: list[dict[str, Any]]
    optional_parameters: list[dict[str, Any]]
    default_capsule_definition_id: PyUUID | None
    graph_template_ref: str | None
    wizard_mode: WizardMode
    constraints: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlanSpecCreate(BaseModel):
    """API model for creating a plan spec"""

    tenant_id: PyUUID
    task_id: PyUUID
    blueprint_definition_id: PyUUID
    blueprint_version: int
    parameters: dict[str, Any]
    capsule_instance_id: PyUUID
    graph_workflow_definition_id: PyUUID
    reasoning_pipelines: list[PyUUID] = Field(default_factory=list)
    created_by_principal_id: PyUUID


class PlanSpecResponse(BaseModel):
    """API model for plan spec response"""

    id: PyUUID
    tenant_id: PyUUID
    task_id: PyUUID
    blueprint_definition_id: PyUUID
    blueprint_version: int
    parameters: dict[str, Any]
    capsule_instance_id: PyUUID
    graph_workflow_definition_id: PyUUID
    reasoning_pipelines: list[PyUUID]
    created_by_principal_id: PyUUID
    created_at: datetime

    class Config:
        from_attributes = True
