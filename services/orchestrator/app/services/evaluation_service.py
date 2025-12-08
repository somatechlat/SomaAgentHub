"""
Evaluation Service - Manages evaluation scenarios, runs, and metrics.

SRS Section 11 - Observability & Evaluation
Handles the definition and execution of evaluation scenarios.
"""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.observability import (
    EvaluationMetricRecord,
    EvaluationMetricRecordCreate,
    EvaluationRun,
    EvaluationRunCreate,
    EvaluationScenarioDefinition,
    EvaluationScenarioDefinitionCreate,
    EvaluationStatus,
)


class EvaluationService:
    """Service for managing evaluations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Scenarios ==========

    async def create_scenario(
        self, scenario_create: EvaluationScenarioDefinitionCreate
    ) -> EvaluationScenarioDefinition:
        """Create a new evaluation scenario"""
        # Check if name exists in tenant
        result = await self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.tenant_id == scenario_create.tenant_id,
                EvaluationScenarioDefinition.name == scenario_create.name,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scenario '{scenario_create.name}' already exists",
            )

        scenario = EvaluationScenarioDefinition(
            tenant_id=scenario_create.tenant_id,
            name=scenario_create.name,
            description=scenario_create.description,
            input_spec=scenario_create.input_spec,
            expected_behavior=scenario_create.expected_behavior,
            metrics_to_compute=scenario_create.metrics_to_compute,
        )

        self.db.add(scenario)
        await self.db.commit()
        await self.db.refresh(scenario)
        return scenario

    async def get_scenario(
        self, scenario_id: UUID, tenant_id: UUID
    ) -> EvaluationScenarioDefinition | None:
        """Get a scenario by ID"""
        result = await self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.id == scenario_id,
                EvaluationScenarioDefinition.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_scenarios(
        self, tenant_id: UUID
    ) -> list[EvaluationScenarioDefinition]:
        """List all scenarios for a tenant"""
        result = await self.db.execute(
            select(EvaluationScenarioDefinition).where(
                EvaluationScenarioDefinition.tenant_id == tenant_id
            )
        )
        return result.scalars().all()

    # ========== Evaluation Runs ==========

    async def create_evaluation_run(
        self, run_create: EvaluationRunCreate
    ) -> EvaluationRun:
        """Start a new evaluation run"""
        # Validate scenario exists
        scenario = await self.get_scenario(run_create.scenario_id, run_create.tenant_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario {run_create.scenario_id} not found",
            )

        run = EvaluationRun(
            tenant_id=run_create.tenant_id,
            scenario_id=run_create.scenario_id,
            status=EvaluationStatus.PENDING,
            evaluated_version_set=run_create.evaluated_version_set,
        )

        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_run(self, run_id: UUID, tenant_id: UUID) -> EvaluationRun | None:
        """Get an evaluation run by ID"""
        result = await self.db.execute(
            select(EvaluationRun).where(
                EvaluationRun.id == run_id, EvaluationRun.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def update_run_status(
        self, run_id: UUID, tenant_id: UUID, status: EvaluationStatus
    ) -> EvaluationRun:
        """Update the status of an evaluation run"""
        run = await self.get_run(run_id, tenant_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found"
            )

        run.status = status
        if status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
            run.finished_at = datetime.utcnow()
        elif status == EvaluationStatus.RUNNING and not run.started_at:
            run.started_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(run)
        return run

    # ========== Metrics ==========

    async def record_metric(
        self, metric_create: EvaluationMetricRecordCreate
    ) -> EvaluationMetricRecord:
        """Record a computed metric for a run"""
        # Validate run exists (omitted for brevity, assume caller has verified context)

        metric = EvaluationMetricRecord(
            evaluation_run_id=metric_create.evaluation_run_id,
            name=metric_create.name,
            value=metric_create.value,
            details_ref=metric_create.details_ref,
        )

        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def get_metrics_for_run(self, run_id: UUID) -> list[EvaluationMetricRecord]:
        """Get all metrics for a specific run"""
        result = await self.db.execute(
            select(EvaluationMetricRecord).where(
                EvaluationMetricRecord.evaluation_run_id == run_id
            )
        )
        return result.scalars().all()
