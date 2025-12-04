"""
Role Service - Manages roles, agent bindings, and session bindings.

SRS Section 5 - Role System
Handles the lifecycle of roles and their binding to specific agents.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from services.common.models.role import (
    RoleDefinition, AgentBinding, AgentSessionBinding, AgentSessionStatus,
    RoleDefinitionCreate, RoleDefinitionResponse,
    AgentBindingCreate, AgentBindingResponse,
    AgentSessionBindingCreate, AgentSessionBindingResponse
)
from services.common.models.identity import ExternalRef, ExternalSystem


class RoleService:
    """Service for managing roles and agent bindings"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Role Definitions ==========

    async def create_role_definition(self, role_create: RoleDefinitionCreate) -> RoleDefinition:
        """Create a new role definition"""
        # Check if name exists in tenant
        result = await self.db.execute(
            select(RoleDefinition).where(
                RoleDefinition.tenant_id == role_create.tenant_id,
                RoleDefinition.name == role_create.name
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role_create.name}' already exists in this tenant"
            )
            
        role = RoleDefinition(
            tenant_id=role_create.tenant_id,
            name=role_create.name,
            description=role_create.description,
            default_persona_ref_id=role_create.default_persona_ref_id,
            expected_behavior=role_create.expected_behavior
        )
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_role_definition(self, role_id: UUID, tenant_id: UUID) -> Optional[RoleDefinition]:
        """Get a role definition by ID"""
        result = await self.db.execute(
            select(RoleDefinition).where(
                RoleDefinition.id == role_id,
                RoleDefinition.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def list_role_definitions(self, tenant_id: UUID) -> List[RoleDefinition]:
        """List all role definitions for a tenant"""
        result = await self.db.execute(
            select(RoleDefinition).where(RoleDefinition.tenant_id == tenant_id)
        )
        return result.scalars().all()

    # ========== Agent Bindings ==========

    async def create_agent_binding(self, binding_create: AgentBindingCreate) -> AgentBinding:
        """Create a binding between a role and an agent implementation"""
        # Validate role exists
        role = await self.get_role_definition(binding_create.role_id, binding_create.tenant_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {binding_create.role_id} not found"
            )
            
        # Validate agent ref exists (Validated by database foreign key constraint)
        
        binding = AgentBinding(
            tenant_id=binding_create.tenant_id,
            role_id=binding_create.role_id,
            agent01_agent_ref_id=binding_create.agent01_agent_ref_id,
            supported_task_types=binding_create.supported_task_types,
            supported_domains=binding_create.supported_domains,
            default_capsule_definition_id=binding_create.default_capsule_definition_id
        )
        
        self.db.add(binding)
        await self.db.commit()
        await self.db.refresh(binding)
        return binding

    async def get_agent_binding(self, binding_id: UUID, tenant_id: UUID) -> Optional[AgentBinding]:
        """Get an agent binding by ID"""
        result = await self.db.execute(
            select(AgentBinding).where(
                AgentBinding.id == binding_id,
                AgentBinding.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def list_bindings_for_role(self, role_id: UUID, tenant_id: UUID) -> List[AgentBinding]:
        """List all bindings for a specific role"""
        result = await self.db.execute(
            select(AgentBinding).where(
                AgentBinding.role_id == role_id,
                AgentBinding.tenant_id == tenant_id
            )
        )
        return result.scalars().all()

    # ========== Agent Session Bindings ==========

    async def create_session_binding(self, session_create: AgentSessionBindingCreate) -> AgentSessionBinding:
        """Create a session binding for a workflow execution"""
        # Validate binding exists
        binding = await self.get_agent_binding(session_create.agent_binding_id, session_create.tenant_id)
        if not binding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent binding {session_create.agent_binding_id} not found"
            )
            
        session = AgentSessionBinding(
            tenant_id=session_create.tenant_id,
            agent_binding_id=session_create.agent_binding_id,
            workflow_instance_id=session_create.workflow_instance_id,
            node_execution_id=session_create.node_execution_id,
            capsule_instance_id=session_create.capsule_instance_id,
            somabrain_persona_ref_id=session_create.somabrain_persona_ref_id,
            somabrain_memory_bank_ref_id=session_create.somabrain_memory_bank_ref_id,
            agent01_session_ref_id=session_create.agent01_session_ref_id,
            status=AgentSessionStatus.OPEN
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def close_session_binding(self, session_id: UUID, tenant_id: UUID) -> AgentSessionBinding:
        """Close an agent session binding"""
        result = await self.db.execute(
            select(AgentSessionBinding).where(
                AgentSessionBinding.id == session_id,
                AgentSessionBinding.tenant_id == tenant_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session binding {session_id} not found"
            )
            
        session.status = AgentSessionStatus.CLOSED
        session.closed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_active_session_for_workflow(self, workflow_instance_id: UUID, role_id: UUID, tenant_id: UUID) -> Optional[AgentSessionBinding]:
        """Find an active session for a workflow and role"""
        # Join AgentSessionBinding -> AgentBinding -> RoleDefinition
        stmt = (
            select(AgentSessionBinding)
            .join(AgentBinding)
            .where(
                AgentSessionBinding.workflow_instance_id == workflow_instance_id,
                AgentSessionBinding.tenant_id == tenant_id,
                AgentSessionBinding.status == AgentSessionStatus.OPEN,
                AgentBinding.role_id == role_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
