"""
Tenant Service - Business logic for tenant management

Handles tenant CRUD operations, validation, and lifecycle management.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.identity import TenantRef, TenantStatus, TenantRefCreate, TenantRefResponse
from services.orchestrator.app.database import get_async_session


class TenantService:
    """Service for managing tenants"""
    
    async def create_tenant(self, tenant_data: TenantRefCreate) -> TenantRefResponse:
        """
        Create a new tenant.
        
        Args:
            tenant_data: Tenant creation data
            
        Returns:
            Created tenant
            
        Raises:
            ValueError: If tenant name already exists
        """
        async with get_async_session() as session:
            # Check if tenant name already exists
            stmt = select(TenantRef).where(TenantRef.name == tenant_data.name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                raise ValueError(f"Tenant with name '{tenant_data.name}' already exists")
            
            # Create new tenant
            tenant = TenantRef(
                name=tenant_data.name,
                status=TenantStatus.ACTIVE
            )
            
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            
            return TenantRefResponse.from_orm(tenant)
    
    async def get_tenant(self, tenant_id: UUID) -> Optional[TenantRefResponse]:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Tenant if found, None otherwise
        """
        async with get_async_session() as session:
            stmt = select(TenantRef).where(TenantRef.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()
            
            if tenant:
                return TenantRefResponse.from_orm(tenant)
            return None
    
    async def list_tenants(self, status: Optional[TenantStatus] = None) -> List[TenantRefResponse]:
        """
        List all tenants, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of tenants
        """
        async with get_async_session() as session:
            stmt = select(TenantRef)
            
            if status:
                stmt = stmt.where(TenantRef.status == status)
            
            stmt = stmt.order_by(TenantRef.created_at.desc())
            
            result = await session.execute(stmt)
            tenants = result.scalars().all()
            
            return [TenantRefResponse.from_orm(t) for t in tenants]
    
    async def update_tenant_status(self, tenant_id: UUID, status: TenantStatus) -> Optional[TenantRefResponse]:
        """
        Update tenant status.
        
        Args:
            tenant_id: Tenant UUID
            status: New status
            
        Returns:
            Updated tenant if found, None otherwise
        """
        async with get_async_session() as session:
            stmt = select(TenantRef).where(TenantRef.id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                return None
            
            tenant.status = status
            await session.commit()
            await session.refresh(tenant)
            
            return TenantRefResponse.from_orm(tenant)
    
    async def delete_tenant(self, tenant_id: UUID) -> bool:
        """
        Soft-delete a tenant (sets status to DELETED).
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.update_tenant_status(tenant_id, TenantStatus.DELETED)
        return result is not None
