from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.identity import (
    TenantRefCreate,
    TenantRefResponse,
    TenantStatus,
)
from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def get_tenant_service(db: AsyncSession = Depends(get_session)) -> TenantService:
    return TenantService(db)


@router.post("/", response_model=TenantRefResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantRefCreate, service: TenantService = Depends(get_tenant_service)
):
    """Create a new tenant"""
    try:
        return await service.create_tenant(tenant_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{tenant_id}", response_model=TenantRefResponse)
async def get_tenant(
    tenant_id: UUID, service: TenantService = Depends(get_tenant_service)
):
    """Get tenant by ID"""
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    return tenant


@router.get("/", response_model=list[TenantRefResponse])
async def list_tenants(
    status: TenantStatus | None = Query(None, description="Filter by tenant status"),
    service: TenantService = Depends(get_tenant_service),
):
    """List all tenants"""
    return await service.list_tenants(status)


@router.patch("/{tenant_id}/status", response_model=TenantRefResponse)
async def update_tenant_status(
    tenant_id: UUID,
    status: TenantStatus,
    service: TenantService = Depends(get_tenant_service),
):
    """Update tenant status"""
    tenant = await service.update_tenant_status(tenant_id, status)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID, service: TenantService = Depends(get_tenant_service)
):
    """Soft delete tenant"""
    success = await service.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
