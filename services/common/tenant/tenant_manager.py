"""
Multi-Tenant Manager for SomaAgentHub
Handles tenant creation, resource management, and access control
"""

from __future__ import annotations

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING = "pending"

    class TenantTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

    @dataclass
    class TenantContext:
    tenant_id: uuid.UUID
    tenant_slug: str
    tier: TenantTier
    status: TenantStatus
    resource_limits: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class TenantResourceQuota:
    max_concurrent_builds: int = 5
    max_agents_per_build: int = 10
    max_build_duration_hours: int = 24
    max_storage_gb: int = 100
    max_cpu_cores: int = 16
    max_memory_gb: int = 32
    max_monthly_cost: float = 1000.0

    class MultiTenantManager:
    def __init__(self):
        self.tenants: Dict[uuid.UUID, TenantContext] = {}
        self.tenant_by_slug: Dict[str, TenantContext] = {}
        self.resource_usage: Dict[uuid.UUID, Dict[str, Any]] = {}
    
    async def create_tenant(
    self,
    name: str,
    slug: str,
    tier: TenantTier = TenantTier.FREE,
    resource_quota: Optional[TenantResourceQuota] = None
    ) -> TenantContext:
        tenant_id = uuid.uuid4()

        if resource_quota is None:
    resource_quota = TenantResourceQuota()

    tenant_context = TenantContext(
    tenant_id=tenant_id,
    tenant_slug=slug,
    tier=tier,
    status=TenantStatus.PENDING,
    resource_limits=resource_quota.__dict__,
    metadata={"created_at": datetime.utcnow().isoformat()}
    )

    self.tenants[tenant_id] = tenant_context
    self.tenant_by_slug[slug] = tenant_context
    self.resource_usage[tenant_id] = {
    "current_builds": 0,
    "current_agents": 0,
    "storage_used_gb": 0,
    "cpu_used_cores": 0,
    "memory_used_gb": 0,
    "monthly_cost": 0.0
    }

    logger.info(f"Created tenant {tenant_id} with slug {slug}")
    return tenant_context
    
    async def get_tenant_context(self, tenant_id: str) -> Optional[TenantContext]:
        try:
    tenant_uuid = uuid.UUID(tenant_id)
    return self.tenants.get(tenant_uuid)
    except ValueError:
    return None
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[TenantContext]:
        return self.tenant_by_slug.get(slug)
    
    async def validate_tenant_access(self, request: Dict[str, Any]) -> TenantContext:
        tenant_id = request.get("tenant_id")
        if not tenant_id:
    raise ValueError("Tenant ID required")

    tenant_context = await self.get_tenant_context(tenant_id)
    if not tenant_context:
    raise ValueError(f"Tenant not found: {tenant_id}")

    if tenant_context.status != TenantStatus.ACTIVE:
    raise ValueError(f"Tenant not active: {tenant_context.status}")

    return tenant_context
    
    async def check_resource_availability(
    self,
    tenant_context: TenantContext,
    resource_request: Dict[str, Any]
    ) -> bool:
        tenant_id = tenant_context.tenant_id
        current_usage = self.resource_usage.get(tenant_id, {})

# Check concurrent builds
        requested_builds = resource_request.get("builds", 0)
        if current_usage.get("current_builds", 0) + requested_builds > tenant_context.resource_limits.get("max_concurrent_builds", 5):
    return False

# Check agents
    requested_agents = resource_request.get("agents", 0)
    if current_usage.get("current_agents", 0) + requested_agents > tenant_context.resource_limits.get("max_agents_per_build", 10):
    return False

    return True
    
    async def allocate_resources(
    self,
    tenant_context: TenantContext,
    resource_allocation: Dict[str, Any]
    ) -> bool:
        tenant_id = tenant_context.tenant_id

        if not await self.check_resource_availability(tenant_context, resource_allocation):
    return False

    current_usage = self.resource_usage.get(tenant_id, {})

# Update resource usage
    current_usage["current_builds"] += resource_allocation.get("builds", 0)
    current_usage["current_agents"] += resource_allocation.get("agents", 0)
    current_usage["storage_used_gb"] += resource_allocation.get("storage_gb", 0)
    current_usage["cpu_used_cores"] += resource_allocation.get("cpu_cores", 0)
    current_usage["memory_used_gb"] += resource_allocation.get("memory_gb", 0)
    current_usage["monthly_cost"] += resource_allocation.get("cost", 0.0)

    self.resource_usage[tenant_id] = current_usage
    logger.info(f"Allocated resources for tenant {tenant_id}: {resource_allocation}")

    return True
    
    async def release_resources(
    self,
    tenant_context: TenantContext,
    resource_allocation: Dict[str, Any]
    ):
        tenant_id = tenant_context.tenant_id
        current_usage = self.resource_usage.get(tenant_id, {})

# Update resource usage
        current_usage["current_builds"] = max(0, current_usage.get("current_builds", 0) - resource_allocation.get("builds", 0))
        current_usage["current_agents"] = max(0, current_usage.get("current_agents", 0) - resource_allocation.get("agents", 0))
        current_usage["storage_used_gb"] = max(0, current_usage.get("storage_used_gb", 0) - resource_allocation.get("storage_gb", 0))
        current_usage["cpu_used_cores"] = max(0, current_usage.get("cpu_used_cores", 0) - resource_allocation.get("cpu_cores", 0))
        current_usage["memory_used_gb"] = max(0, current_usage.get("memory_used_gb", 0) - resource_allocation.get("memory_gb", 0))
        current_usage["monthly_cost"] = max(0, current_usage.get("monthly_cost", 0.0) - resource_allocation.get("cost", 0.0))

        self.resource_usage[tenant_id] = current_usage
        logger.info(f"Released resources for tenant {tenant_id}: {resource_allocation}")
    
    async def get_resource_usage(self, tenant_context: TenantContext) -> Dict[str, Any]:
        return self.resource_usage.get(tenant_context.tenant_id, {})
    
    async def list_tenants(self) -> List[TenantContext]:
        return list(self.tenants.values())
    
    async def update_tenant_status(
    self,
    tenant_id: str,
    status: TenantStatus
    ) -> Optional[TenantContext]:
        tenant_context = await self.get_tenant_context(tenant_id)
        if tenant_context:
    tenant_context.status = status
    logger.info(f"Updated tenant {tenant_id} status to {status}")
    return tenant_context
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        tenant_context = await self.get_tenant_context(tenant_id)
        if tenant_context:
    # Remove from data structures
    del self.tenants[tenant_context.tenant_id]
    del self.tenant_by_slug[tenant_context.tenant_slug]
    if tenant_context.tenant_id in self.resource_usage:
        del self.resource_usage[tenant_context.tenant_id]
    
    logger.info(f"Deleted tenant {tenant_id}")
    return True
    return False