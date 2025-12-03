"""
Tasks API - Endpoints for managing tasks.

SRS Section 4 - Task Management
Exposes task creation, retrieval, and status management via REST API.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.task_service import TaskService
from services.common.models.task import (
    TaskRecord, TaskStatus,
    TaskRecordCreate, TaskRecordResponse
)
# In a real implementation, we would extract tenant_id from the auth token
# For now, we accept it as a header or query param for demonstration
from fastapi import Header

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db: Session = Depends(get_db)) -> TaskService:
    return TaskService(db)


@router.post("/", response_model=TaskRecordResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_create: TaskRecordCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service)
):
    """Create a new task"""
    # Enforce tenant isolation: ensure request tenant matches header
    if task_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch between header and body"
        )
        
    return service.create_task(task_create)


@router.get("/{task_id}", response_model=TaskRecordResponse)
def get_task(
    task_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service)
):
    """Get a task by ID"""
    task = service.get_task(task_id, x_tenant_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.get("/", response_model=List[TaskRecordResponse])
def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service)
):
    """List all tasks for a tenant"""
    return service.list_tasks(x_tenant_id, status)


@router.patch("/{task_id}/status", response_model=TaskRecordResponse)
def update_task_status(
    task_id: UUID,
    status: TaskStatus,
    reason: Optional[str] = None,
    actor_principal_id: Optional[UUID] = None,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service)
):
    """Update a task's status"""
    try:
        return service.update_task_status(
            task_id, x_tenant_id, status, reason, actor_principal_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_task(
    task_id: UUID,
    reason: str = Query(..., min_length=1),
    actor_principal_id: Optional[UUID] = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service)
):
    """Cancel a task"""
    try:
        service.cancel_task(task_id, x_tenant_id, reason, actor_principal_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
