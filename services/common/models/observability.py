"""
Observability and Evaluation Models

SRS Section 11 - Observability, Evaluation & Audit
Span indexing, evaluation scenarios, and metrics tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# Enums
class SpanStatus(str, Enum):
    """OpenTelemetry span status"""

    OK = "OK"
    ERROR = "ERROR"


class Component(str, Enum):
    """System component"""

    HUB = "HUB"
    AGENT01 = "AGENT01"
    SOMABRAIN = "SOMABRAIN"
    TOOL = "TOOL"
    EXTERNAL = "EXTERNAL"


class EvaluationStatus(str, Enum):
    """Evaluation run status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Models
class SomaTraceSpanSummary(Base):
    """
    Hub-side index of OpenTelemetry trace spans.

    SRS Section 11.1 - SomaTraceSpanSummary
    Full traces in OTEL backend; Hub keeps summarized index.
    """

    __tablename__ = "soma_trace_span_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Trace identifiers
    trace_id = Column(Text, nullable=False, index=True)
    span_id = Column(Text, nullable=False, index=True)
    parent_span_id = Column(Text, nullable=True)

    # Component and operation
    component = Column(SQLEnum(Component), nullable=False, index=True)
    operation_name = Column(Text, nullable=False, index=True)

    # Status
    status = Column(SQLEnum(SpanStatus), nullable=False)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    latency_ms = Column(Float, nullable=False)

    # Attributes (relevant context)
    attributes = Column(
        JSONB, nullable=False, default=dict
    )  # task_id, node_id, role_id, capsule_id, etc.

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class EvaluationScenarioDefinition(Base):
    """
    Reusable evaluation scenario for regression testing.

    SRS Section 11.2 - EvaluationScenarioDefinition
    Test cases for workflow validation.
    """

    __tablename__ = "evaluation_scenario_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Test specification
    input_spec = Column(JSONB, nullable=False)  # Description/pointer to input set
    expected_behavior = Column(Text, nullable=False)  # High-level description
    metrics_to_compute = Column(
        JSONB, nullable=False, default=list
    )  # e.g., pass@k, accuracy, cost

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class EvaluationRun(Base):
    """
    Single evaluation run of a scenario.

    SRS Section 11.3 - EvaluationRun
    Tracks execution of evaluation scenarios.
    """

    __tablename__ = "evaluation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_scenario_definitions.id"),
        nullable=False,
        index=True,
    )

    # Status
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SQLEnum(EvaluationStatus),
        nullable=False,
        default=EvaluationStatus.PENDING,
        index=True,
    )

    # Version tracking
    evaluated_version_set = Column(
        JSONB, nullable=False
    )  # Which blueprint, Capsule, agents tested

    # Results stored in metrics table
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class EvaluationMetricRecord(Base):
    """
    Single metric from an evaluation run.

    SRS Section 11.4 - EvaluationMetricRecord
    Individual metrics like accuracy, latency, cost.
    """

    __tablename__ = "evaluation_metric_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_run_id = Column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)  # e.g., "accuracy", "avg_latency"
    value = Column(Float, nullable=False)
    details_ref = Column(Text, nullable=True)  # Pointer to per-case breakdown

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


# Pydantic models



class SomaTraceSpanSummaryCreate(BaseModel):
    """API model for creating a trace span summary"""

    tenant_id: PyUUID
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    component: Component
    operation_name: str
    status: SpanStatus
    start_time: datetime
    end_time: datetime
    latency_ms: float
    attributes: dict[str, Any] = Field(default_factory=dict)


class SomaTraceSpanSummaryResponse(BaseModel):
    """API model for trace span summary response"""

    id: PyUUID
    tenant_id: PyUUID
    trace_id: str
    span_id: str
    parent_span_id: str | None
    component: Component
    operation_name: str
    status: SpanStatus
    start_time: datetime
    end_time: datetime
    latency_ms: float
    attributes: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationScenarioDefinitionCreate(BaseModel):
    """API model for creating an evaluation scenario"""

    tenant_id: PyUUID
    name: str
    description: str | None = None
    input_spec: dict[str, Any]
    expected_behavior: str
    metrics_to_compute: list[str] = Field(default_factory=list)


class EvaluationScenarioDefinitionResponse(BaseModel):
    """API model for evaluation scenario response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    description: str | None
    input_spec: dict[str, Any]
    expected_behavior: str
    metrics_to_compute: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluationRunCreate(BaseModel):
    """API model for creating an evaluation run"""

    tenant_id: PyUUID
    scenario_id: PyUUID
    evaluated_version_set: dict[str, Any]


class EvaluationRunResponse(BaseModel):
    """API model for evaluation run response"""

    id: PyUUID
    tenant_id: PyUUID
    scenario_id: PyUUID
    started_at: datetime
    finished_at: datetime | None
    status: EvaluationStatus
    evaluated_version_set: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationMetricRecordCreate(BaseModel):
    """API model for creating a metric record"""

    evaluation_run_id: PyUUID
    name: str
    value: float
    details_ref: str | None = None


class EvaluationMetricRecordResponse(BaseModel):
    """API model for metric record response"""

    id: PyUUID
    evaluation_run_id: PyUUID
    name: str
    value: float
    details_ref: str | None
    created_at: datetime

    class Config:
        from_attributes = True
