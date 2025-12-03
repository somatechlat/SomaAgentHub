"""
Roles API - Endpoints for managing roles and agent bindings.

SRS Section 5 - Role System
Exposes role definition and binding management via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.role_service import RoleService
from services.common.models.role import (
    RoleDefinitionCreate, RoleDefinitionResponse,
    AgentBindingCreate, AgentBindingResponse
)

router = APIRouter(prefix="/roles", tags=["roles"])


def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    return RoleService(db)


@router.post("/", response_model=RoleDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_role(
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
    return service.create_role_definition(role_create)


@router.get("/{role_id}", response_model=RoleDefinitionResponse)
def get_role(
    role_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """Get a role definition by ID"""
    role = service.get_role_definition(role_id, x_tenant_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found"
        )
    return role


@router.get("/", response_model=List[RoleDefinitionResponse])
def list_roles(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """List all role definitions for a tenant"""
    return service.list_role_definitions(x_tenant_id)


@router.post("/bindings", response_model=AgentBindingResponse, status_code=status.HTTP_201_CREATED)
def create_binding(
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
    return service.create_agent_binding(binding_create)


@router.get("/{role_id}/bindings", response_model=List[AgentBindingResponse])
def list_bindings(
    role_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RoleService = Depends(get_role_service)
):
    """List all bindings for a specific role"""
    return service.list_bindings_for_role(role_id, x_tenant_id)
