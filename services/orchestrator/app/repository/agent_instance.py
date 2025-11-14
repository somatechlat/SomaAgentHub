"""Repository for AgentInstance operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.agent_instance import AgentInstance, AgentStatus


class AgentInstanceRepository:
    """Repository for managing agent instances."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_agent_instance(
        self,
        agent_type: str,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        k8s_namespace: str,
        capsule_id: Optional[uuid.UUID] = None,
        resource_requests: Optional[dict] = None,
        resource_limits: Optional[dict] = None,
        metadata: Optional[dict] = None
    ) -> AgentInstance:
        """Create a new agent instance."""
        instance = AgentInstance(
            agent_type=agent_type,
            capsule_id=capsule_id,
            tenant_id=tenant_id,
            user_id=user_id,
            k8s_namespace=k8s_namespace,
            resource_requests=resource_requests or {},
            resource_limits=resource_limits or {},
            metadata=metadata or {}
        )
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_agent_instance(self, instance_id: uuid.UUID) -> Optional[AgentInstance]:
        """Get agent instance by ID."""
        stmt = select(AgentInstance).where(AgentInstance.id == instance_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_agent_status(
        self,
        instance_id: uuid.UUID,
        status: AgentStatus,
        k8s_job_name: Optional[str] = None,
        k8s_deployment_name: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[AgentInstance]:
        """Update agent status and Kubernetes details."""
        stmt = select(AgentInstance).where(AgentInstance.id == instance_id)
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if instance:
            instance.status = status
            if k8s_job_name:
                instance.k8s_job_name = k8s_job_name
            if k8s_deployment_name:
                instance.k8s_deployment_name = k8s_deployment_name
            if error_message:
                instance.error_message = error_message
            if metadata:
                instance.metadata.update(metadata)
            
            if status == AgentStatus.RUNNING:
                instance.started_at = datetime.utcnow()
            elif status in [AgentStatus.SUCCEEDED, AgentStatus.FAILED, AgentStatus.TERMINATED]:
                instance.completed_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(instance)
        
        return instance
    
    async def list_agent_instances(
        self,
        tenant_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[AgentStatus] = None,
        agent_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentInstance]:
        """List agent instances with filtering."""
        stmt = select(AgentInstance)
        
        if tenant_id:
            stmt = stmt.where(AgentInstance.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(AgentInstance.user_id == user_id)
        if status:
            stmt = stmt.where(AgentInstance.status == status)
        if agent_type:
            stmt = stmt.where(AgentInstance.agent_type == agent_type)
            
        stmt = stmt.order_by(AgentInstance.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_running_agents(self, tenant_id: uuid.UUID) -> List[AgentInstance]:
        """Get all running agents for a tenant."""
        stmt = select(AgentInstance).where(
            AgentInstance.tenant_id == tenant_id,
            AgentInstance.status == AgentStatus.RUNNING
        ).order_by(AgentInstance.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def terminate_agents_by_user(
        self,
        user_id: uuid.UUID,
        reason: str = "User requested termination"
    ) -> int:
        """Terminate all agents for a user."""
        stmt = (
            update(AgentInstance)
            .where(
                AgentInstance.user_id == user_id,
                AgentInstance.status.in_([AgentStatus.PENDING, AgentStatus.RUNNING])
            )
            .values(
                status=AgentStatus.TERMINATED,
                error_message=reason,
                completed_at=datetime.utcnow()
            )
            .returning(AgentInstance.id)
        )
        result = await self.session.execute(stmt)
        return len(result.fetchall())
    
    async def count_agents_by_status(
        self,
        tenant_id: uuid.UUID,
        status: AgentStatus
    ) -> int:
        """Count agents by status for a tenant."""
        stmt = select(AgentInstance).where(
            AgentInstance.tenant_id == tenant_id,
            AgentInstance.status == status
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())