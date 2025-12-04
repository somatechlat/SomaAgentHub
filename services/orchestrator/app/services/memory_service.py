"""
Memory Service - Manages memory bindings and operation records.

SRS Section 7 - Memory Integration
Handles binding tasks to memory contexts and recording memory operations.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.memory import (
    MemoryBindingSpec, MemoryOperationRecord,
    MemoryOperationType, MemoryBindingSpecCreate,
    MemoryOperationRecordCreate
)


class MemoryService:
    """Service for managing memory bindings and operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Memory Bindings ==========

    async def create_binding_spec(self, spec_create: MemoryBindingSpecCreate) -> MemoryBindingSpec:
        """Create a new memory binding specification"""
        # Validate workflow instance exists (would check WorkflowService)
        
        binding = MemoryBindingSpec(
            tenant_id=spec_create.tenant_id,
            task_id=spec_create.task_id,
            workflow_instance_id=spec_create.workflow_instance_id,
            somabrain_memory_bank_refs=spec_create.somabrain_memory_bank_refs,
            somabrain_example_store_ref_id=spec_create.somabrain_example_store_ref_id,
            scopes=spec_create.scopes or {},
            write_policy=spec_create.write_policy or {},
            read_policy=spec_create.read_policy or {}
        )
        
        self.db.add(binding)
        await self.db.commit()
        await self.db.refresh(binding)
        return binding

    async def get_binding_spec(self, binding_id: UUID, tenant_id: UUID) -> Optional[MemoryBindingSpec]:
        """Get a memory binding spec by ID"""
        result = await self.db.execute(
            select(MemoryBindingSpec).where(
                MemoryBindingSpec.id == binding_id,
                MemoryBindingSpec.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def get_binding_for_workflow(self, workflow_instance_id: UUID, tenant_id: UUID) -> Optional[MemoryBindingSpec]:
        """Get the memory binding for a specific workflow instance"""
        result = await self.db.execute(
            select(MemoryBindingSpec).where(
                MemoryBindingSpec.workflow_instance_id == workflow_instance_id,
                MemoryBindingSpec.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    # ========== Memory Operations ==========

    async def record_operation(self, op_create: MemoryOperationRecordCreate) -> MemoryOperationRecord:
        """Record a memory operation (read/write)"""
        # Validate binding exists for context
        binding = await self.get_binding_for_workflow(op_create.workflow_instance_id, op_create.tenant_id)
        if not binding:
            # Depending on policy, might allow unbound operations or require binding
            # For now, we log it but don't block, assuming ad-hoc memory access is possible
            pass
            
        record = MemoryOperationRecord(
            tenant_id=op_create.tenant_id,
            workflow_instance_id=op_create.workflow_instance_id,
            node_execution_id=op_create.node_execution_id,
            operation_type=op_create.operation_type,
            somabrain_ref_id=op_create.somabrain_ref_id,
            request_summary=op_create.request_summary,
            response_summary=op_create.response_summary,
            policy_decision=op_create.policy_decision
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_operations_for_workflow(self, workflow_instance_id: UUID, tenant_id: UUID) -> List[MemoryOperationRecord]:
        """List all memory operations for a workflow"""
        result = await self.db.execute(
            select(MemoryOperationRecord).where(
                MemoryOperationRecord.workflow_instance_id == workflow_instance_id,
                MemoryOperationRecord.tenant_id == tenant_id
            ).order_by(MemoryOperationRecord.created_at)
        )
        return result.scalars().all()
