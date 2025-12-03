"""
Memory API - Endpoints for managing memory bindings and operations.

SRS Section 7 - Memory Integration
Exposes memory binding and operation tracking via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.memory_service import MemoryService
from services.common.models.memory import (
    MemoryBindingSpecCreate, MemoryBindingSpecResponse,
    MemoryOperationRecordCreate, MemoryOperationRecordResponse
)

router = APIRouter(prefix="/memory", tags=["memory"])


def get_memory_service(db: Session = Depends(get_db)) -> MemoryService:
    return MemoryService(db)


@router.post("/bindings", response_model=MemoryBindingSpecResponse, status_code=status.HTTP_201_CREATED)
def create_binding(
    binding_create: MemoryBindingSpecCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """Create a new memory binding specification"""
    if binding_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_binding_spec(binding_create)


@router.get("/bindings/{binding_id}", response_model=MemoryBindingSpecResponse)
def get_binding(
    binding_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """Get a memory binding by ID"""
    binding = service.get_binding_spec(binding_id, x_tenant_id)
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Binding {binding_id} not found"
        )
    return binding


@router.post("/operations", response_model=MemoryOperationRecordResponse, status_code=status.HTTP_201_CREATED)
def record_operation(
    op_create: MemoryOperationRecordCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """Record a memory operation"""
    if op_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.record_operation(op_create)


@router.get("/operations/workflow/{workflow_instance_id}", response_model=List[MemoryOperationRecordResponse])
def list_operations(
    workflow_instance_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: MemoryService = Depends(get_memory_service)
):
    """List all memory operations for a workflow"""
    return service.list_operations_for_workflow(workflow_instance_id, x_tenant_id)
