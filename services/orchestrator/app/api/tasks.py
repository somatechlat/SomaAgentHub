"""
Tasks API - Endpoints for managing tasks.

SRS Section 4 - Task Management
Exposes task creation, retrieval, and status management via REST API.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.task import (
    TaskRecordCreate,
    TaskRecordResponse,
    TaskRecordUpdate,
    TaskStatus,
)
from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(db: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(db)


@router.post(
    "/", response_model=TaskRecordResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    task_create: TaskRecordCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service),
):
    """Create a new task"""
    # Enforce tenant isolation: ensure request tenant matches header
    if task_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch between header and body",
        )

    return await service.create_task(task_create)


@router.get("/{task_id}", response_model=TaskRecordResponse)
async def get_task(
    task_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service),
):
    """Get a task by ID"""
    task = await service.get_task(task_id, x_tenant_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    return task


@router.get("/", response_model=list[TaskRecordResponse])
async def list_tasks(
    status: TaskStatus | None = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service),
):
    """List all tasks for a tenant"""
    return await service.list_tasks(tenant_id=x_tenant_id, status=status)


@router.patch("/{task_id}/status", response_model=TaskRecordResponse)
async def update_task_status(
    task_id: UUID,
    status: TaskStatus,
    reason: str | None = None,
    actor_principal_id: UUID | None = None,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service),
):
    """Update a task's status"""
    update_data = TaskRecordUpdate(
        status=status, reason=reason, actor_principal_id=actor_principal_id
    )
    task = await service.update_task_status(task_id, x_tenant_id, update_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: UUID,
    reason: str = Query(..., min_length=1),
    actor_principal_id: UUID | None = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: TaskService = Depends(get_task_service),
):
    """Cancel a task"""
    update_data = TaskRecordUpdate(
        status=TaskStatus.CANCELLED,
        reason=reason,
        actor_principal_id=actor_principal_id,
    )
    task = await service.update_task_status(task_id, x_tenant_id, update_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )
