"""
Tenants API - Endpoints for managing tenants.

SRS Section 1 - Identity & Multi-Tenancy
Exposes tenant management functionality via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.tenant_service import TenantService
from services.common.models.identity import (
    TenantRef, TenantStatus,
    TenantRefCreate, TenantRefResponse
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


@router.post("/", response_model=TenantRefResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_create: TenantRefCreate,
    service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant"""
    return service.create_tenant(tenant_create)


@router.get("/{tenant_id}", response_model=TenantRefResponse)
def get_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service)
):
    """Get a tenant by ID"""
    tenant = service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    return tenant


@router.get("/", response_model=List[TenantRefResponse])
def list_tenants(
    service: TenantService = Depends(get_tenant_service)
):
    """List all tenants"""
    # Note: In a real system, this would be restricted to super-admins
    return service.list_tenants()


@router.patch("/{tenant_id}/status", response_model=TenantRefResponse)
def update_tenant_status(
    tenant_id: UUID,
    status: TenantStatus,
    service: TenantService = Depends(get_tenant_service)
):
    """Update a tenant's status"""
    try:
        return service.update_tenant_status(tenant_id, status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
