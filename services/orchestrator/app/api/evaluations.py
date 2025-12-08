"""
Evaluation API - Endpoints for managing evaluations.

SRS Section 11 - Observability & Evaluation
Exposes evaluation scenario and run management via REST API.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.observability import (
    EvaluationMetricRecordResponse,
    EvaluationRunCreate,
    EvaluationRunResponse,
    EvaluationScenarioDefinitionCreate,
    EvaluationScenarioDefinitionResponse,
)
from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def get_evaluation_service(
    db: AsyncSession = Depends(get_session),
) -> EvaluationService:
    return EvaluationService(db)


@router.post(
    "/scenarios",
    response_model=EvaluationScenarioDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    scenario_create: EvaluationScenarioDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Create a new evaluation scenario"""
    if scenario_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch"
        )
    return await service.create_scenario(scenario_create)


@router.get(
    "/scenarios/{scenario_id}", response_model=EvaluationScenarioDefinitionResponse
)
async def get_scenario(
    scenario_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Get a scenario by ID"""
    scenario = await service.get_scenario(scenario_id, x_tenant_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )
    return scenario


@router.get("/scenarios", response_model=list[EvaluationScenarioDefinitionResponse])
async def list_scenarios(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """List all scenarios for a tenant"""
    return await service.list_scenarios(x_tenant_id)


@router.post(
    "/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED
)
async def create_run(
    run_create: EvaluationRunCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Start a new evaluation run"""
    if run_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch"
        )
    return await service.create_evaluation_run(run_create)


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Get an evaluation run by ID"""
    run = await service.get_run(run_id, x_tenant_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found"
        )
    return run


@router.get(
    "/runs/{run_id}/metrics", response_model=list[EvaluationMetricRecordResponse]
)
async def get_run_metrics(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Get metrics for a specific run"""
    # Validate run access first
    run = await service.get_run(run_id, x_tenant_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found"
        )
    return await service.get_metrics_for_run(run_id)
