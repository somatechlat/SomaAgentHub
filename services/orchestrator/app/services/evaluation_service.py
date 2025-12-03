"""
Evaluation Service - Manages evaluation scenarios, runs, and metrics.

SRS Section 11 - Observability & Evaluation
Handles the definition and execution of evaluation scenarios.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.observability import (
    EvaluationScenarioDefinition, EvaluationRun, EvaluationMetricRecord,
    EvaluationStatus, EvaluationScenarioDefinitionCreate,
    EvaluationRunCreate, EvaluationMetricRecordCreate
)


class EvaluationService:
    """Service for managing evaluations"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Scenarios ==========

    def create_scenario(self, scenario_create: EvaluationScenarioDefinitionCreate) -> EvaluationScenarioDefinition:
        """Create a new evaluation scenario"""
        # Check if name exists in tenant
        existing = self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.tenant_id == scenario_create.tenant_id,
                EvaluationScenarioDefinition.name == scenario_create.name
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scenario '{scenario_create.name}' already exists"
            )
            
        scenario = EvaluationScenarioDefinition(
            tenant_id=scenario_create.tenant_id,
            name=scenario_create.name,
            description=scenario_create.description,
            input_spec=scenario_create.input_spec,
            expected_behavior=scenario_create.expected_behavior,
            metrics_to_compute=scenario_create.metrics_to_compute
        )
        
        self.db.add(scenario)
        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    def get_scenario(self, scenario_id: UUID, tenant_id: UUID) -> Optional[EvaluationScenarioDefinition]:
        """Get a scenario by ID"""
        return self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.id == scenario_id,
                EvaluationScenarioDefinition.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    def list_scenarios(self, tenant_id: UUID) -> List[EvaluationScenarioDefinition]:
        """List all scenarios for a tenant"""
        return self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.tenant_id == tenant_id
            )
        ).scalars().all()

    # ========== Evaluation Runs ==========

    def create_evaluation_run(self, run_create: EvaluationRunCreate) -> EvaluationRun:
        """Start a new evaluation run"""
        # Validate scenario exists
        scenario = self.get_scenario(run_create.scenario_id, run_create.tenant_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {run_create.scenario_id} not found"
            )
            
        run = EvaluationRun(
            tenant_id=run_create.tenant_id,
            scenario_id=run_create.scenario_id,
            status=EvaluationStatus.PENDING,
            evaluated_version_set=run_create.evaluated_version_set
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: UUID, tenant_id: UUID) -> Optional[EvaluationRun]:
        """Get an evaluation run by ID"""
        return self.db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == run_id,
                EvaluationRun.tenant_id == tenant_id
            )
        ).scalar_one_or_none()

    def update_run_status(self, run_id: UUID, tenant_id: UUID, status: EvaluationStatus) -> EvaluationRun:
        """Update the status of an evaluation run"""
        run = self.get_run(run_id, tenant_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {run_id} not found"
            )
            
        run.status = status
        if status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
            run.finished_at = datetime.utcnow()
        elif status == EvaluationStatus.RUNNING and not run.started_at:
            run.started_at = datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(run)
        return run

    # ========== Metrics ==========

    def record_metric(self, metric_create: EvaluationMetricRecordCreate) -> EvaluationMetricRecord:
        """Record a computed metric for a run"""
        # Validate run exists (omitted for brevity, assume caller has verified context)
        
        metric = EvaluationMetricRecord(
            evaluation_run_id=metric_create.evaluation_run_id,
            name=metric_create.name,
            value=metric_create.value,
            details_ref=metric_create.details_ref
        )
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_metrics_for_run(self, run_id: UUID) -> List[EvaluationMetricRecord]:
        """Get all metrics for a specific run"""
        return self.db.execute(
            select(EvaluationMetricRecord).where(
                EvaluationMetricRecord.evaluation_run_id == run_id
            )
        ).scalars().all()
