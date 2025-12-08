"""
HITL API - Endpoints for managing human-in-the-loop workflows.

SRS Section 10 - Human-in-the-Loop (HITL)
Exposes reviewer assignment and decision recording via REST API.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.hitl import (
    HumanDecisionRecordCreate,
    HumanDecisionRecordResponse,
    HumanReviewerAssignmentCreate,
    HumanReviewerAssignmentResponse,
)
from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.hitl_service import HITLService

router = APIRouter(prefix="/hitl", tags=["hitl"])


def get_hitl_service(db: AsyncSession = Depends(get_session)) -> HITLService:
    return HITLService(db)


@router.post(
    "/assignments",
    response_model=HumanReviewerAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_reviewer(
    assignment_create: HumanReviewerAssignmentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: HITLService = Depends(get_hitl_service),
):
    """Assign a reviewer to a session"""
    if assignment_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch"
        )
    return await service.assign_reviewer(assignment_create)


@router.get(
    "/assignments/{assignment_id}", response_model=HumanReviewerAssignmentResponse
)
async def get_assignment(
    assignment_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: HITLService = Depends(get_hitl_service),
):
    """Get an assignment by ID"""
    assignment = await service.get_assignment(assignment_id, x_tenant_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment {assignment_id} not found",
        )
    return assignment


@router.post(
    "/decisions",
    response_model=HumanDecisionRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_decision(
    decision_create: HumanDecisionRecordCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: HITLService = Depends(get_hitl_service),
):
    """Record a reviewer's decision"""
    if decision_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch"
        )
    return await service.record_decision(decision_create)


@router.get(
    "/decisions/session/{session_id}", response_model=list[HumanDecisionRecordResponse]
)
async def list_decisions(
    session_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: HITLService = Depends(get_hitl_service),
):
    """List all decisions for a session"""
    return await service.get_decisions_for_session(session_id, x_tenant_id)
