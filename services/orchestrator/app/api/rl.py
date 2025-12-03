"""
RL API - Endpoints for managing RL/MARL infrastructure.

SRS Sections 8-9 - RL/MARL Infrastructure
Exposes reasoning pipeline, game, and trajectory management via REST API.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from services.orchestrator.app.database import get_db
from services.orchestrator.app.services.rl_service import RLService
from services.common.models.rl import (
    ReasoningPipelineSpecCreate, ReasoningPipelineSpecResponse,
    GameSpecCreate, GameSpecResponse,
    TrajectoryRecordCreate, TrajectoryRecordResponse,
    RLExportJobCreate, RLExportJobResponse
)

router = APIRouter(prefix="/rl", tags=["rl"])


def get_rl_service(db: Session = Depends(get_db)) -> RLService:
    return RLService(db)


@router.post("/pipelines", response_model=ReasoningPipelineSpecResponse, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    pipeline_create: ReasoningPipelineSpecCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Create a new reasoning pipeline specification"""
    if pipeline_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_reasoning_pipeline(pipeline_create)


@router.get("/pipelines/{pipeline_id}", response_model=ReasoningPipelineSpecResponse)
def get_pipeline(
    pipeline_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Get a reasoning pipeline by ID"""
    pipeline = service.get_reasoning_pipeline(pipeline_id, x_tenant_id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline {pipeline_id} not found"
        )
    return pipeline


@router.post("/games", response_model=GameSpecResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    game_create: GameSpecCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Create a new game specification"""
    if game_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_game_spec(game_create)


@router.get("/games/{game_id}", response_model=GameSpecResponse)
def get_game(
    game_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Get a game spec by ID"""
    game = service.get_game_spec(game_id, x_tenant_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    return game


@router.post("/trajectories", response_model=TrajectoryRecordResponse, status_code=status.HTTP_201_CREATED)
def record_trajectory(
    trajectory_create: TrajectoryRecordCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Record a completed trajectory"""
    if trajectory_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.record_trajectory(trajectory_create)


@router.get("/trajectories/{trajectory_id}", response_model=TrajectoryRecordResponse)
def get_trajectory(
    trajectory_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Get a trajectory record by ID"""
    trajectory = service.get_trajectory(trajectory_id, x_tenant_id)
    if not trajectory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trajectory {trajectory_id} not found"
        )
    return trajectory


@router.post("/exports", response_model=RLExportJobResponse, status_code=status.HTTP_201_CREATED)
def create_export_job(
    job_create: RLExportJobCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: RLService = Depends(get_rl_service)
):
    """Create a new RL export job"""
    if job_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return service.create_export_job(job_create)
