"""
Roles API - Endpoints for managing roles and agent bindings.

SRS Section 5 - Role System
Exposes role definition and binding management via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.role_service import RoleService
from services.common.models.role import (
    RoleDefinitionCreate, RoleDefinitionResponse,
    AgentBindingCreate, AgentBindingResponse
)

router = APIRouter(prefix="/roles", tags=["roles"])


def get_role_service(db: AsyncSession = Depends(get_session)) -> RoleService:
    return RoleService(db)


@router.post("/", response_model=RoleDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_create: RoleDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """Create a new role definition"""
    if role_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_role_definition(role_create)


@router.get("/{role_id}", response_model=RoleDefinitionResponse)
async def get_role(
    role_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """Get a role definition by ID"""
    role = await service.get_role_definition(role_id, x_tenant_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found"
        )
    return role


@router.get("/", response_model=List[RoleDefinitionResponse])
async def list_roles(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """List all role definitions for a tenant"""
    return await service.list_role_definitions(x_tenant_id)


@router.post("/bindings", response_model=AgentBindingResponse, status_code=status.HTTP_201_CREATED)
async def create_binding(
    binding_create: AgentBindingCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """Create a binding between a role and an agent"""
    if binding_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_agent_binding(binding_create)


@router.get("/{role_id}/bindings", response_model=List[AgentBindingResponse])
async def list_bindings(
    role_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """List all bindings for a specific role"""
    return await service.list_bindings_for_role(role_id, x_tenant_id)
