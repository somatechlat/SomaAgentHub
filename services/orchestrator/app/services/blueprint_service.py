"""
Blueprint Service - Manages blueprints and plan generation.

SRS Section 3 - Blueprint System
Handles the definition of task blueprints and the generation of execution plans.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.blueprint import (
    BlueprintDefinition, PlanSpec, BlueprintStatus,
    BlueprintDefinitionCreate, PlanSpecCreate
)


class BlueprintService:
    """Service for managing blueprints and plans"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Blueprint Definitions ==========

    def create_blueprint(self, blueprint_create: BlueprintDefinitionCreate) -> BlueprintDefinition:
        """Create a new blueprint definition"""
        # Check if name exists in tenant
        existing = self.db.execute(
            select(BlueprintDefinition).where(
                BlueprintDefinition.tenant_id == blueprint_create.tenant_id,
                BlueprintDefinition.name == blueprint_create.name,
                BlueprintDefinition.version == blueprint_create.version
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Blueprint '{blueprint_create.name}' version '{blueprint_create.version}' already exists"
            )
            
        blueprint = BlueprintDefinition(
            tenant_id=blueprint_create.tenant_id,
            name=blueprint_create.name,
            version=blueprint_create.version,
            status=blueprint_create.status,
            description=blueprint_create.description,
            supported_task_types=blueprint_create.supported_task_types,
            required_parameters=blueprint_create.required_parameters,
            optional_parameters=blueprint_create.optional_parameters,
            default_capsule_definition_id=blueprint_create.default_capsule_definition_id,
            graph_template_ref=blueprint_create.graph_template_ref,
            wizard_mode=blueprint_create.wizard_mode,
            constraints=blueprint_create.constraints
        )
        
        self.db.add(blueprint)
        self.db.commit()
        self.db.refresh(blueprint)
        return blueprint

    def get_blueprint(self, blueprint_id: UUID, tenant_id: UUID) -> Optional[BlueprintDefinition]:
        """Get a blueprint by ID"""
        return self.db.execute(
            select(BlueprintDefinition).where(
                BlueprintDefinition.id == blueprint_id,
                BlueprintDefinition.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    def list_blueprints(self, tenant_id: UUID, status_filter: Optional[BlueprintStatus] = None) -> List[BlueprintDefinition]:
        """List all blueprints for a tenant"""
        query = select(BlueprintDefinition).where(BlueprintDefinition.tenant_id == tenant_id)
        if status_filter:
            query = query.where(BlueprintDefinition.status == status_filter)
        return self.db.execute(query).scalars().all()

    # ========== Plans ==========

    def create_plan_spec(self, plan_create: PlanSpecCreate) -> PlanSpec:
        """Create a new execution plan from a blueprint"""
        # Validate blueprint exists
        blueprint = self.get_blueprint(plan_create.blueprint_definition_id, plan_create.tenant_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blueprint {plan_create.blueprint_definition_id} not found"
            )
            
        # Validate parameters against blueprint schema (placeholder for full JSON schema validation)
        # validate_parameters(plan_create.parameters, blueprint.required_parameters)
        
        plan = PlanSpec(
            tenant_id=plan_create.tenant_id,
            task_id=plan_create.task_id,
            blueprint_definition_id=plan_create.blueprint_definition_id,
            blueprint_version=plan_create.blueprint_version,
            parameters=plan_create.parameters,
            capsule_instance_id=plan_create.capsule_instance_id,
            graph_workflow_definition_id=plan_create.graph_workflow_definition_id,
            reasoning_pipelines=plan_create.reasoning_pipelines,
            created_by_principal_id=plan_create.created_by_principal_id
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan(self, plan_id: UUID, tenant_id: UUID) -> Optional[PlanSpec]:
        """Get a plan by ID"""
        return self.db.execute(
            select(PlanSpec).where(
                PlanSpec.id == plan_id,
                PlanSpec.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    def get_plan_for_task(self, task_id: UUID, tenant_id: UUID) -> Optional[PlanSpec]:
        """Get the plan associated with a task"""
        return self.db.execute(
            select(PlanSpec).where(
                PlanSpec.task_id == task_id,
                PlanSpec.tenant_id == tenant_id
            )
        ).scalar_one_or_none()
