"""Pydantic schemas for analytics service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class CapsuleRunRequest(BaseModel):
    capsule_id: str
    tenant_id: str
    persona: str
    success: bool
    tokens: int
    revisions: int = 0
    duration_seconds: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CapsuleRunAggregate(BaseModel):
    capsule_id: str
    tenant_id: str
    total_runs: int
    success_rate: float
    avg_tokens: float
    avg_revisions: float
    avg_duration_seconds: float


class CapsuleDashboardResponse(BaseModel):
    aggregates: List[CapsuleRunAggregate]
    window: str


class PersonaRegressionRequest(BaseModel):
    persona_id: str
    tenant_id: str
    trigger_reason: Optional[str] = None


class PersonaRegressionResponse(BaseModel):
    persona_id: str
    tenant_id: str
    status: str
    last_run_at: Optional[datetime]
    notes: List[str]
    queued_at: Optional[datetime] = None
    running_at: Optional[datetime] = None
    last_error: Optional[str] = None


class AnomalyRecord(BaseModel):
    capsule_id: str
    tenant_id: str
    metric: str
    current_value: float
    threshold: float
    message: str


class AnomalyResponse(BaseModel):
    anomalies: List[AnomalyRecord]


class GovernanceReportResponse(BaseModel):
    report_id: str
    tenant_id: str
    generated_at: datetime
    summary: str
    changes: List[str]


class GovernanceReportRequest(BaseModel):
    tenant_id: str
    summary: str
    changes: List[str]


class NotificationLog(BaseModel):
    tenant_id: str
    message: str
    timestamp: str


class NotificationFeed(BaseModel):
    notifications: List[NotificationLog]


class KamachiqRunRequest(BaseModel):
    tenant_id: str
    name: str
    deliverable_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KamachiqRunResponse(BaseModel):
    run_id: str
    tenant_id: str
    name: str
    deliverable_count: int
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingEventRequest(BaseModel):
    tenant_id: str
    service: str
    cost: float
    currency: str | None = None
    tokens: int = 0
    capsule_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    event_id: Optional[str] = None


class BillingLedgerEntry(BaseModel):
    tenant_id: str
    capsule_id: Optional[str]
    service: str
    currency: str
    total_tokens: int
    total_cost: float
    event_count: int
    last_recorded_at: datetime


class BillingLedgerResponse(BaseModel):
    entries: List[BillingLedgerEntry]


class PersonaRegressionTransitionRequest(BaseModel):
    tenant_id: str
    persona_id: str
    status: Literal["queued", "running", "completed", "failed"]
    note: Optional[str] = None
    error: Optional[str] = None


class DisasterRecoveryDrillRequest(BaseModel):
    primary_region: str
    failover_region: str
    started_at: datetime
    ended_at: datetime
    rpo_seconds: float
    succeeded: bool = True
    notes: Optional[str] = None


class DisasterRecoveryDrillResponse(BaseModel):
    drill_id: str
    primary_region: str
    failover_region: str
    started_at: datetime
    ended_at: datetime
    rto_seconds: float
    rpo_seconds: float
    succeeded: bool
    notes: Optional[str] = None


class BenchmarkRunRequest(BaseModel):
    suite: str
    scenario: str
    service: str
    target: str
    started_at: datetime
    completed_at: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None


class BenchmarkRunResponse(BaseModel):
    benchmark_id: str
    suite: str
    scenario: str
    service: str
    target: str
    started_at: datetime
    completed_at: datetime
    score: float
    metrics: Dict[str, float]
    metadata: Dict[str, str]
    tenant_id: Optional[str] = None


class BenchmarkCollectionResponse(BaseModel):
    results: List[BenchmarkRunResponse]


class BenchmarkScoreboardEntry(BaseModel):
    scenario: str
    attempts: int
    best_service: str
    best_score: float
    best_benchmark_id: str
    average_latency_p95_ms: float
    average_requests_per_second: float
    average_error_rate: float


class BenchmarkScoreboardResponse(BaseModel):
    scoreboard: List[BenchmarkScoreboardEntry]


class AgentOneSightDashboardResponse(BaseModel):
    generated_at: datetime
    tenant_id: Optional[str]
    capsule_dashboard: CapsuleDashboardResponse
    anomalies: List[AnomalyRecord]
    benchmark_scoreboard: List[BenchmarkScoreboardEntry]
    billing_ledger: BillingLedgerResponse
    kamachiq_summary: Dict[str, Any]
    disaster_summary: Dict[str, Any]
    notifications: List[NotificationLog]
    regressions_due: List[PersonaRegressionResponse]
