"""
Tenant Service - Business logic for tenant management

Handles tenant CRUD operations, validation, and lifecycle management.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.identity import (
    TenantRef,
    TenantRefCreate,
    TenantRefResponse,
    TenantStatus,
)
from services.orchestrator.app.database import get_async_session


class TenantService:
    """Service for managing tenants"""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session

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
        if self.session:
            return await self._create_tenant_impl(self.session, tenant_data)
        async with get_async_session() as session:
            return await self._create_tenant_impl(session, tenant_data)

    async def _create_tenant_impl(
        self, session: AsyncSession, tenant_data: TenantRefCreate
    ) -> TenantRefResponse:
        # Check if tenant name already exists
        stmt = select(TenantRef).where(TenantRef.name == tenant_data.name)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Tenant with name '{tenant_data.name}' already exists")

        # Create new tenant
        tenant = TenantRef(name=tenant_data.name, status=TenantStatus.ACTIVE)

        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        return TenantRefResponse.from_orm(tenant)

    async def get_tenant(self, tenant_id: UUID) -> TenantRefResponse | None:
        """
        Get tenant by ID.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant if found, None otherwise
        """
        if self.session:
            return await self._get_tenant_impl(self.session, tenant_id)
        async with get_async_session() as session:
            return await self._get_tenant_impl(session, tenant_id)

    async def _get_tenant_impl(
        self, session: AsyncSession, tenant_id: UUID
    ) -> TenantRefResponse | None:
        stmt = select(TenantRef).where(TenantRef.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant:
            return TenantRefResponse.from_orm(tenant)
        return None

    async def list_tenants(
        self, status: TenantStatus | None = None
    ) -> list[TenantRefResponse]:
        """
        List all tenants, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of tenants
        """
        if self.session:
            return await self._list_tenants_impl(self.session, status)
        async with get_async_session() as session:
            return await self._list_tenants_impl(session, status)

    async def _list_tenants_impl(
        self, session: AsyncSession, status: TenantStatus | None
    ) -> list[TenantRefResponse]:
        stmt = select(TenantRef)

        if status:
            stmt = stmt.where(TenantRef.status == status)

        stmt = stmt.order_by(TenantRef.created_at.desc())

        result = await session.execute(stmt)
        tenants = result.scalars().all()

        return [TenantRefResponse.from_orm(t) for t in tenants]

    async def update_tenant_status(
        self, tenant_id: UUID, status: TenantStatus
    ) -> TenantRefResponse | None:
        """
        Update tenant status.

        Args:
            tenant_id: Tenant UUID
            status: New status

        Returns:
            Updated tenant if found, None otherwise
        """
        if self.session:
            return await self._update_tenant_status_impl(
                self.session, tenant_id, status
            )
        async with get_async_session() as session:
            return await self._update_tenant_status_impl(session, tenant_id, status)

    async def _update_tenant_status_impl(
        self, session: AsyncSession, tenant_id: UUID, status: TenantStatus
    ) -> TenantRefResponse | None:
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
