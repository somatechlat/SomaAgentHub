"""
RL Service - Manages reasoning pipelines, games, and trajectory recording.

SRS Sections 8-9 - RL/MARL Infrastructure
Handles the definition of RL components and the collection of training data.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.rl import (
    ReasoningPipelineSpec, GameSpec, TrajectoryRecord, RLExportJob,
    TrajectoryOutcome, RLExportStatus,
    ReasoningPipelineSpecCreate, GameSpecCreate,
    TrajectoryRecordCreate, RLExportJobCreate
)


class RLService:
    """Service for managing RL/MARL infrastructure"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Reasoning Pipelines ==========

    def create_reasoning_pipeline(self, pipeline_create: ReasoningPipelineSpecCreate) -> ReasoningPipelineSpec:
        """Create a new reasoning pipeline specification"""
        # Check if name exists in tenant
        existing = self.db.execute(
            select(ReasoningPipelineSpec).where(
                ReasoningPipelineSpec.tenant_id == pipeline_create.tenant_id,
                ReasoningPipelineSpec.name == pipeline_create.name,
                ReasoningPipelineSpec.version == pipeline_create.version
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Pipeline '{pipeline_create.name}' version '{pipeline_create.version}' already exists"
            )
            
        pipeline = ReasoningPipelineSpec(
            tenant_id=pipeline_create.tenant_id,
            name=pipeline_create.name,
            version=pipeline_create.version,
            description=pipeline_create.description,
            pipeline_type=pipeline_create.pipeline_type,
            stages=pipeline_create.stages,
            max_iterations=pipeline_create.max_iterations,
            sampling_policy=pipeline_create.sampling_policy
        )
        
        self.db.add(pipeline)
        self.db.commit()
        self.db.refresh(pipeline)
        return pipeline

    def get_reasoning_pipeline(self, pipeline_id: UUID, tenant_id: UUID) -> Optional[ReasoningPipelineSpec]:
        """Get a reasoning pipeline by ID"""
        return self.db.execute(
            select(ReasoningPipelineSpec).where(
                ReasoningPipelineSpec.id == pipeline_id,
                ReasoningPipelineSpec.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    # ========== Game Specs ==========

    def create_game_spec(self, game_create: GameSpecCreate) -> GameSpec:
        """Create a new game specification"""
        existing = self.db.execute(
            select(GameSpec).where(
                GameSpec.tenant_id == game_create.tenant_id,
                GameSpec.name == game_create.name,
                GameSpec.version == game_create.version
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Game '{game_create.name}' version '{game_create.version}' already exists"
            )
            
        game = GameSpec(
            tenant_id=game_create.tenant_id,
            name=game_create.name,
            version=game_create.version,
            description=game_create.description,
            players=game_create.players,
            game_type=game_create.game_type,
            equilibrium_target=game_create.equilibrium_target,
            payoff_definitions=game_create.payoff_definitions,
            exploitability_tolerance=game_create.exploitability_tolerance,
            capsule_constraints=game_create.capsule_constraints
        )
        
        self.db.add(game)
        self.db.commit()
        self.db.refresh(game)
        return game

    def get_game_spec(self, game_id: UUID, tenant_id: UUID) -> Optional[GameSpec]:
        """Get a game spec by ID"""
        return self.db.execute(
            select(GameSpec).where(
                GameSpec.id == game_id,
                GameSpec.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    # ========== Trajectories ==========

    def record_trajectory(self, trajectory_create: TrajectoryRecordCreate) -> TrajectoryRecord:
        """Record a completed trajectory"""
        # Validate task/workflow exists (omitted for brevity)
        
        trajectory = TrajectoryRecord(
            tenant_id=trajectory_create.tenant_id,
            task_id=trajectory_create.task_id,
            workflow_instance_id=trajectory_create.workflow_instance_id,
            reasoning_pipeline_id=trajectory_create.reasoning_pipeline_id,
            game_spec_id=trajectory_create.game_spec_id,
            capsule_instance_id=trajectory_create.capsule_instance_id,
            final_outcome=trajectory_create.final_outcome,
            global_reward=trajectory_create.global_reward,
            role_returns=trajectory_create.role_returns,
            meta=trajectory_create.meta or {},
            storage_ref=trajectory_create.storage_ref
        )
        
        self.db.add(trajectory)
        self.db.commit()
        self.db.refresh(trajectory)
        return trajectory

    def get_trajectory(self, trajectory_id: UUID, tenant_id: UUID) -> Optional[TrajectoryRecord]:
        """Get a trajectory record by ID"""
        return self.db.execute(
            select(TrajectoryRecord).where(
                TrajectoryRecord.id == trajectory_id,
                TrajectoryRecord.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    # ========== Export Jobs ==========

    def create_export_job(self, job_create: RLExportJobCreate) -> RLExportJob:
        """Create a new RL export job"""
        job = RLExportJob(
            tenant_id=job_create.tenant_id,
            requested_by_principal_id=job_create.requested_by_principal_id,
            filter_criteria=job_create.filter_criteria,
            status=RLExportStatus.PENDING
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_export_job(self, job_id: UUID, tenant_id: UUID) -> Optional[RLExportJob]:
        """Get an export job by ID"""
        return self.db.execute(
            select(RLExportJob).where(
                RLExportJob.id == job_id,
                RLExportJob.tenant_id == tenant_id
            )
        ).scalar_one_or_none()
