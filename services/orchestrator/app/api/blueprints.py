"""
Blueprints API - Endpoints for managing blueprints and plans.

SRS Section 3 - Blueprint System
Exposes blueprint definition and plan generation via REST API.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.blueprint_service import BlueprintService
from services.common.models.blueprint import (
    BlueprintDefinitionCreate, BlueprintDefinitionResponse,
    PlanSpecCreate, PlanSpecResponse,
    BlueprintStatus
)

router = APIRouter(prefix="/blueprints", tags=["blueprints"])


def get_blueprint_service(db: AsyncSession = Depends(get_session)) -> BlueprintService:
    return BlueprintService(db)


@router.post("/", response_model=BlueprintDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    blueprint_create: BlueprintDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: BlueprintService = Depends(get_blueprint_service)
):
    """Create a new blueprint definition"""
    if blueprint_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_blueprint(blueprint_create)


@router.get("/{blueprint_id}", response_model=BlueprintDefinitionResponse)
async def get_blueprint(
    blueprint_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: BlueprintService = Depends(get_blueprint_service)
):
    """Get a blueprint by ID"""
    blueprint = await service.get_blueprint(blueprint_id, x_tenant_id)
    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found"
        )
    return blueprint


@router.get("/", response_model=List[BlueprintDefinitionResponse])
async def list_blueprints(
    status: Optional[BlueprintStatus] = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: BlueprintService = Depends(get_blueprint_service)
):
    """List all blueprints for a tenant"""
    return await service.list_blueprints(x_tenant_id, status)


@router.post("/plans", response_model=PlanSpecResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_create: PlanSpecCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: BlueprintService = Depends(get_blueprint_service)
):
    """Create a new execution plan from a blueprint"""
    if plan_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_plan_spec(plan_create)


@router.get("/plans/{plan_id}", response_model=PlanSpecResponse)
async def get_plan(
    plan_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: BlueprintService = Depends(get_blueprint_service)
):
    """Get a plan by ID"""
    plan = await service.get_plan(plan_id, x_tenant_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found"
        )
    return plan
