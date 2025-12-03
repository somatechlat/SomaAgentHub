"""
Evaluation API - Endpoints for managing evaluations.

SRS Section 11 - Observability & Evaluation
Exposes evaluation scenario and run management via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.evaluation_service import EvaluationService
from services.common.models.observability import (
    EvaluationScenarioDefinitionCreate, EvaluationScenarioDefinitionResponse,
    EvaluationRunCreate, EvaluationRunResponse,
    EvaluationMetricRecordResponse
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db)


@router.post("/scenarios", response_model=EvaluationScenarioDefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario_create: EvaluationScenarioDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Create a new evaluation scenario"""
    if scenario_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_scenario(scenario_create)


@router.get("/scenarios/{scenario_id}", response_model=EvaluationScenarioDefinitionResponse)
def get_scenario(
    scenario_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Get a scenario by ID"""
    scenario = service.get_scenario(scenario_id, x_tenant_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found"
        )
    return scenario


@router.get("/scenarios", response_model=List[EvaluationScenarioDefinitionResponse])
def list_scenarios(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """List all scenarios for a tenant"""
    return service.list_scenarios(x_tenant_id)


@router.post("/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def create_run(
    run_create: EvaluationRunCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Start a new evaluation run"""
    if run_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_evaluation_run(run_create)


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
def get_run(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Get an evaluation run by ID"""
    run = service.get_run(run_id, x_tenant_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found"
        )
    return run


@router.get("/runs/{run_id}/metrics", response_model=List[EvaluationMetricRecordResponse])
def get_run_metrics(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Get metrics for a specific run"""
    # Validate run access first
    run = service.get_run(run_id, x_tenant_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found"
        )
    return service.get_metrics_for_run(run_id)
