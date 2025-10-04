"""REST endpoints for analytics service."""

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from ..core.config import get_settings
from ..core.metrics import KAMACHIQ_RUNS_TOTAL
from ..core.store import (
    BillingEvent,
    CapsuleRun,
    DisasterRecoveryDrill,
    GovernanceReport,
    KamachiqRun,
    BenchmarkResult,
    store,
)
from .schemas import (
    AnomalyRecord,
    AnomalyResponse,
    BillingEventRequest,
    BillingLedgerEntry,
    BillingLedgerResponse,
    CapsuleDashboardResponse,
    CapsuleRunAggregate,
    CapsuleRunRequest,
    KamachiqRunRequest,
    KamachiqRunResponse,
    GovernanceReportRequest,
    GovernanceReportResponse,
    NotificationFeed,
    NotificationLog,
    PersonaRegressionRequest,
    PersonaRegressionResponse,
    PersonaRegressionTransitionRequest,
    DisasterRecoveryDrillRequest,
    DisasterRecoveryDrillResponse,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    BenchmarkCollectionResponse,
    BenchmarkScoreboardEntry,
    BenchmarkScoreboardResponse,
    AgentOneSightDashboardResponse,
)

router = APIRouter(prefix="/v1", tags=["analytics"])


def _calculate_benchmark_score(metrics: Dict[str, float]) -> float:
    settings = get_settings()
    latency = metrics.get("latency_p95_ms")
    throughput = metrics.get("requests_per_second")
    error_rate = metrics.get("error_rate")

    latency_component = 1.0
    if latency and latency > 0:
        latency_component = min(settings.benchmark_latency_target_ms / latency, 2.0)

    throughput_component = 0.0
    if throughput and throughput > 0:
        throughput_component = min(throughput / settings.benchmark_throughput_target_rps, 2.0)

    error_component = 1.0
    if error_rate is not None:
        denominator = max(settings.benchmark_error_budget, 1e-6)
        error_component = max(0.0, 1.0 - (error_rate / denominator))
        error_component = min(error_component, 2.0)

    score = (latency_component + throughput_component + error_component) / 3.0
    return round(score, 4)


@router.post("/benchmarks/run", response_model=BenchmarkRunResponse, status_code=status.HTTP_201_CREATED)
def record_benchmark_run(payload: BenchmarkRunRequest) -> BenchmarkRunResponse:
    metrics: Dict[str, float] = {}
    for key, value in payload.metrics.items():
        try:
            metrics[key] = float(value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Metric '{key}' must be numeric")

    metadata = {key: str(value) for key, value in payload.metadata.items()}
    benchmark = BenchmarkResult(
        benchmark_id=str(uuid.uuid4()),
        suite=payload.suite,
        scenario=payload.scenario,
        service=payload.service,
        target=payload.target,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        score=_calculate_benchmark_score(metrics),
        metrics=metrics,
        metadata=metadata,
        tenant_id=payload.tenant_id,
    )
    store.record_benchmark(benchmark)
    return BenchmarkRunResponse(
        benchmark_id=benchmark.benchmark_id,
        suite=benchmark.suite,
        scenario=benchmark.scenario,
        service=benchmark.service,
        target=benchmark.target,
        started_at=benchmark.started_at,
        completed_at=benchmark.completed_at,
        score=benchmark.score,
        metrics=benchmark.metrics,
        metadata=benchmark.metadata,
        tenant_id=benchmark.tenant_id,
    )


@router.get("/benchmarks/latest", response_model=BenchmarkCollectionResponse)
def latest_benchmarks(
    suite: str | None = None,
    scenario: str | None = None,
    tenant_id: str | None = None,
    limit: int = 20,
) -> BenchmarkCollectionResponse:
    results = store.list_benchmarks(suite=suite, scenario=scenario, tenant_id=tenant_id)
    results.sort(key=lambda result: result.completed_at)
    if limit and limit > 0:
        results = results[-limit:]

    payload = [
        BenchmarkRunResponse(
            benchmark_id=result.benchmark_id,
            suite=result.suite,
            scenario=result.scenario,
            service=result.service,
            target=result.target,
            started_at=result.started_at,
            completed_at=result.completed_at,
            score=result.score,
            metrics=result.metrics,
            metadata=result.metadata,
            tenant_id=result.tenant_id,
        )
        for result in results
    ]
    return BenchmarkCollectionResponse(results=payload)


@router.get("/benchmarks/scoreboard", response_model=BenchmarkScoreboardResponse)
def benchmark_scoreboard(
    suite: str | None = None,
    tenant_id: str | None = None,
) -> BenchmarkScoreboardResponse:
    entries = [
        BenchmarkScoreboardEntry(**record)
        for record in store.benchmark_scoreboard(suite=suite, tenant_id=tenant_id)
    ]
    return BenchmarkScoreboardResponse(scoreboard=entries)


@router.get("/dashboards/agent-one-sight", response_model=AgentOneSightDashboardResponse)
def agent_one_sight_dashboard(
    tenant_id: str | None = None,
    capsule_window_hours: int | None = None,
    benchmark_suite: str | None = None,
    notification_limit: int = 10,
) -> AgentOneSightDashboardResponse:
    capsule_data = capsule_dashboard(tenant_id=tenant_id, window_hours=capsule_window_hours)
    anomaly_records = detect_anomalies().anomalies
    if tenant_id:
        anomaly_records = [record for record in anomaly_records if record.tenant_id == tenant_id]

    benchmarks = [
        BenchmarkScoreboardEntry(**entry)
        for entry in store.benchmark_scoreboard(suite=benchmark_suite, tenant_id=tenant_id)
    ]

    ledger = billing_ledger(tenant_id=tenant_id)

    notifications_raw = store.notifications[-notification_limit:] if notification_limit > 0 else store.notifications
    notifications = [NotificationLog(**entry) for entry in notifications_raw[-notification_limit:]] if notification_limit > 0 else [NotificationLog(**entry) for entry in notifications_raw]

    regressions = store.pending_regressions()
    if tenant_id:
        regressions = [reg for reg in regressions if reg.tenant_id == tenant_id]
    regressions_due = [PersonaRegressionResponse(**reg.__dict__) for reg in regressions]

    return AgentOneSightDashboardResponse(
        generated_at=datetime.utcnow(),
        tenant_id=tenant_id,
        capsule_dashboard=capsule_data,
        anomalies=anomaly_records,
        benchmark_scoreboard=benchmarks,
        billing_ledger=ledger,
        kamachiq_summary=store.kamachiq_summary(),
        disaster_summary=store.drill_summary(),
        notifications=notifications,
        regressions_due=regressions_due,
    )


@router.post("/capsule-runs", status_code=status.HTTP_202_ACCEPTED)
def record_capsule_run(payload: CapsuleRunRequest) -> dict[str, str]:
    """Ingest capsule execution metrics for later aggregation."""

    run = CapsuleRun(
        capsule_id=payload.capsule_id,
        tenant_id=payload.tenant_id,
        persona=payload.persona,
        success=payload.success,
        tokens=payload.tokens,
        revisions=payload.revisions,
        duration_seconds=payload.duration_seconds,
        recorded_at=datetime.utcnow(),
    )
    store.record_run(run)
    if not payload.success:
        store.log_notification(payload.tenant_id, f"Capsule {payload.capsule_id} reported a failure event")
    return {"status": "accepted"}


@router.get("/dashboards/capsules", response_model=CapsuleDashboardResponse)
def capsule_dashboard(
    tenant_id: str | None = None,
    window_hours: int | None = None,
) -> CapsuleDashboardResponse:
    """Return aggregate capsule metrics for dashboards."""

    runs = store.list_runs()
    if tenant_id:
        runs = [run for run in runs if run.tenant_id == tenant_id]
    if window_hours:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        runs = [run for run in runs if run.recorded_at >= cutoff]
    grouped: Dict[tuple[str, str], List[CapsuleRun]] = {}
    for run in runs:
        grouped.setdefault((run.tenant_id, run.capsule_id), []).append(run)

    aggregates: List[CapsuleRunAggregate] = []
    for (tenant_id, capsule_id), items in grouped.items():
        total_runs = len(items)
        success_rate = sum(1 for item in items if item.success) / total_runs if total_runs else 0.0
        avg_tokens = statistics.fmean(item.tokens for item in items)
        avg_revisions = statistics.fmean(item.revisions for item in items)
        avg_duration = statistics.fmean(item.duration_seconds for item in items)
        aggregates.append(
            CapsuleRunAggregate(
                capsule_id=capsule_id,
                tenant_id=tenant_id,
                total_runs=total_runs,
                success_rate=round(success_rate, 3),
                avg_tokens=round(avg_tokens, 2),
                avg_revisions=round(avg_revisions, 2),
                avg_duration_seconds=round(avg_duration, 2),
            )
        )

    if window_hours and tenant_id:
        window = f"tenant_last_{window_hours}h"
    elif window_hours:
        window = f"last_{window_hours}h"
    elif tenant_id:
        window = "tenant"
    else:
        window = "last_1000_runs"
    return CapsuleDashboardResponse(aggregates=aggregates, window=window)


@router.get("/anomalies", response_model=AnomalyResponse)
def detect_anomalies() -> AnomalyResponse:
    """Highlight capsules that violate baseline success thresholds."""

    settings = get_settings()
    anomalies: List[AnomalyRecord] = []
    for aggregate in capsule_dashboard().aggregates:
        if aggregate.success_rate < settings.anomaly_threshold:
            anomalies.append(
                AnomalyRecord(
                    capsule_id=aggregate.capsule_id,
                    tenant_id=aggregate.tenant_id,
                    metric="success_rate",
                    current_value=aggregate.success_rate,
                    threshold=settings.anomaly_threshold,
                    message="Success rate below policy threshold",
                )
            )
    return AnomalyResponse(anomalies=anomalies)


@router.post("/anomalies/scan", response_model=AnomalyResponse)
def scan_anomalies() -> AnomalyResponse:
    """Run anomaly detection and emit notifications for concerning capsules."""

    response = detect_anomalies()
    for record in response.anomalies:
        message = (
            f"Capsule {record.capsule_id} for tenant {record.tenant_id} below {record.metric} threshold "
            f"({record.current_value:.3f} < {record.threshold:.3f})"
        )
        store.log_notification(record.tenant_id, message)
    return response


@router.post("/persona-regressions/run", response_model=PersonaRegressionResponse)
def run_persona_regression(payload: PersonaRegressionRequest) -> PersonaRegressionResponse:
    """Record persona regression evaluation results and surface notifications."""

    note = payload.trigger_reason or "Scheduled evaluation"
    regression = store.transition_regression(
        persona_id=payload.persona_id,
        tenant_id=payload.tenant_id,
        status="completed",
        note=note,
    )
    store.log_notification(payload.tenant_id, f"Persona {payload.persona_id} regression completed")
    return PersonaRegressionResponse(**regression.__dict__)


@router.post("/persona-regressions/transition", response_model=PersonaRegressionResponse)
def transition_persona_regression(
    payload: PersonaRegressionTransitionRequest,
) -> PersonaRegressionResponse:
    """Update regression state machine (queued, running, completed, failed)."""

    regression = store.transition_regression(
        persona_id=payload.persona_id,
        tenant_id=payload.tenant_id,
        status=payload.status,
        note=payload.note,
        error=payload.error,
    )

    message: str | None = None
    if payload.status == "queued":
        message = f"Persona {payload.persona_id} regression queued"
    elif payload.status == "running":
        message = f"Persona {payload.persona_id} regression running"
    elif payload.status == "completed":
        message = f"Persona {payload.persona_id} regression completed"
    elif payload.status == "failed":
        err = payload.error or payload.note or "unknown error"
        message = f"Persona {payload.persona_id} regression failed: {err}"

    if message:
        store.log_notification(payload.tenant_id, message)

    return PersonaRegressionResponse(**regression.__dict__)


@router.get("/persona-regressions", response_model=List[PersonaRegressionResponse])
def list_regressions() -> List[PersonaRegressionResponse]:
    return [PersonaRegressionResponse(**reg.__dict__) for reg in store.list_regressions()]


@router.get("/persona-regressions/due", response_model=List[PersonaRegressionResponse])
def due_regressions() -> List[PersonaRegressionResponse]:
    return [PersonaRegressionResponse(**reg.__dict__) for reg in store.pending_regressions()]


@router.post("/governance/reports", response_model=GovernanceReportResponse, status_code=status.HTTP_201_CREATED)
def create_governance_report(payload: GovernanceReportRequest) -> GovernanceReportResponse:
    report = GovernanceReport(
        report_id=str(uuid.uuid4()),
        tenant_id=payload.tenant_id,
        generated_at=datetime.utcnow(),
        summary=payload.summary,
        changes=payload.changes,
    )
    store.store_governance_report(report)
    store.log_notification(payload.tenant_id, "Governance report generated")
    return GovernanceReportResponse(**report.__dict__)


@router.get("/governance/reports", response_model=List[GovernanceReportResponse])
def list_governance_reports(tenant_id: str | None = None) -> List[GovernanceReportResponse]:
    reports = store.list_reports(tenant_id)
    return [GovernanceReportResponse(**report.__dict__) for report in reports]


@router.get("/notifications", response_model=NotificationFeed)
def notification_feed() -> NotificationFeed:
    notifications = [NotificationLog(**entry) for entry in store.notifications]
    return NotificationFeed(notifications=notifications)


@router.post("/kamachiq/runs", response_model=KamachiqRunResponse, status_code=status.HTTP_201_CREATED)
def record_kamachiq_run(payload: KamachiqRunRequest) -> KamachiqRunResponse:
    run = KamachiqRun(
        run_id=str(uuid.uuid4()),
        tenant_id=payload.tenant_id,
        name=payload.name,
        deliverable_count=payload.deliverable_count,
        created_at=datetime.utcnow(),
        metadata={k: str(v) for k, v in payload.metadata.items()},
    )
    store.record_kamachiq_run(run)
    store.log_notification(payload.tenant_id, f"KAMACHIQ run '{payload.name}' recorded")
    KAMACHIQ_RUNS_TOTAL.labels(tenant=payload.tenant_id).inc()
    return KamachiqRunResponse(**run.__dict__)


@router.get("/kamachiq/runs", response_model=List[KamachiqRunResponse])
def list_kamachiq_runs(tenant_id: str | None = None) -> List[KamachiqRunResponse]:
    runs = store.list_kamachiq_runs(tenant_id)
    return [KamachiqRunResponse(**run.__dict__) for run in runs]


@router.get("/kamachiq/summary")
def kamachiq_summary() -> Dict[str, Any]:
    summary = store.kamachiq_summary()
    last = summary.get("last_run")
    if last and hasattr(last, "__dict__"):
        summary["last_run"] = last.__dict__
    return summary


@router.post("/kamachiq/blocked", status_code=status.HTTP_202_ACCEPTED)
def record_blocked_deliverable(data: Dict[str, str]) -> dict[str, str]:
    tenant_id = data.get("tenant_id", "unknown")
    message = data.get("message") or "KAMACHIQ deliverable blocked"
    store.record_blocked_deliverable(data)
    store.log_notification(tenant_id, message)
    return {"status": "accepted"}


@router.post("/kamachiq/resolved", status_code=status.HTTP_202_ACCEPTED)
def record_resolved_deliverable(data: Dict[str, str]) -> dict[str, str]:
    tenant_id = data.get("tenant_id", "unknown")
    message = data.get("message") or "KAMACHIQ deliverable resolved"
    store.record_resolved_deliverable(data)
    store.log_notification(tenant_id, message)
    return {"status": "accepted"}


@router.post("/billing/events", status_code=status.HTTP_202_ACCEPTED)
def record_billing_event(payload: BillingEventRequest) -> dict[str, str]:
    """Ingest billing events (tokens + cost) for downstream ledger aggregation."""

    settings = get_settings()
    currency = payload.currency or settings.billing_default_currency
    event_id = payload.event_id or str(uuid.uuid4())
    event = BillingEvent(
        event_id=event_id,
        tenant_id=payload.tenant_id,
        service=payload.service,
        capsule_id=payload.capsule_id,
        tokens=payload.tokens,
        cost=float(payload.cost),
        currency=currency,
        recorded_at=datetime.utcnow(),
        metadata={k: str(v) for k, v in payload.metadata.items()},
    )
    store.record_billing_event(event)
    if event.cost >= settings.billing_alert_threshold:
        store.log_notification(
            payload.tenant_id,
            f"Billing event exceeded threshold ({event.cost:.2f} {currency}) for {event.service}",
        )
    return {"status": "accepted", "event_id": event_id}


@router.get("/billing/ledgers", response_model=BillingLedgerResponse)
def billing_ledger(tenant_id: str | None = None) -> BillingLedgerResponse:
    """Aggregate billing totals per tenant/capsule/service."""

    aggregates = store.aggregate_billing(tenant_id)
    entries: List[BillingLedgerEntry] = []
    for record in aggregates:
        entries.append(
            BillingLedgerEntry(
                tenant_id=record["tenant_id"],
                capsule_id=record["capsule_id"],
                service=record["service"],
                currency=record["currency"],
                total_tokens=record["total_tokens"],
                total_cost=round(record["total_cost"], 4),
                event_count=record["event_count"],
                last_recorded_at=record["last_recorded_at"],
            )
        )
    entries.sort(key=lambda entry: (entry.tenant_id, entry.capsule_id or "", entry.service))
    return BillingLedgerResponse(entries=entries)


@router.post(
    "/drills/disaster",
    response_model=DisasterRecoveryDrillResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_disaster_drill(payload: DisasterRecoveryDrillRequest) -> DisasterRecoveryDrillResponse:
    """Record the outcome of a disaster recovery drill with RTO/RPO metrics."""

    rto_seconds = (payload.ended_at - payload.started_at).total_seconds()
    drill = DisasterRecoveryDrill(
        drill_id=str(uuid.uuid4()),
        primary_region=payload.primary_region,
        failover_region=payload.failover_region,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        rto_seconds=rto_seconds,
        rpo_seconds=payload.rpo_seconds,
        succeeded=payload.succeeded,
        notes=payload.notes,
    )
    store.record_drill(drill)
    if not payload.succeeded:
        store.log_notification(
            "ops",
            f"DR drill failed for {payload.primary_region} -> {payload.failover_region}",
        )
    return DisasterRecoveryDrillResponse(**drill.__dict__)


@router.get("/drills/disaster", response_model=List[DisasterRecoveryDrillResponse])
def list_disaster_drills() -> List[DisasterRecoveryDrillResponse]:
    """List recorded disaster recovery drills."""

    return [
        DisasterRecoveryDrillResponse(**drill.__dict__)
        for drill in store.list_drills()
    ]


@router.get("/drills/disaster/summary")
def disaster_drill_summary() -> Dict[str, Any]:
    """Return aggregate metrics for disaster recovery drills."""

    summary = store.drill_summary()
    # Ensure dict serialization for nested last_drill dataclass
    last = summary.get("last_drill")
    if last and hasattr(last, "__dict__"):
        summary["last_drill"] = last.__dict__
    return summary


@router.get("/exports/capsule-runs")
def export_capsule_runs(
    tenant_id: str | None = None,
    window_hours: int | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Return capsule run logs as JSON for downstream ingestion."""

    runs = store.list_runs()
    if tenant_id:
        runs = [run for run in runs if run.tenant_id == tenant_id]
    if window_hours:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        runs = [run for run in runs if run.recorded_at >= cutoff]

    payload = [
        {
            "capsule_id": run.capsule_id,
            "tenant_id": run.tenant_id,
            "persona": run.persona,
            "success": run.success,
            "tokens": run.tokens,
            "revisions": run.revisions,
            "duration_seconds": run.duration_seconds,
            "recorded_at": run.recorded_at.isoformat(),
        }
        for run in runs
    ]
    return {"runs": payload}


@router.get("/exports/billing-ledger")
def export_billing_ledger(tenant_id: str | None = None) -> Dict[str, List[Dict[str, Any]]]:
    """Return aggregated billing ledger as JSON."""

    aggregates = store.aggregate_billing(tenant_id)
    payload = [
        {
            "tenant_id": record["tenant_id"],
            "capsule_id": record["capsule_id"],
            "service": record["service"],
            "currency": record["currency"],
            "total_tokens": record["total_tokens"],
            "total_cost": round(record["total_cost"], 4),
            "event_count": record["event_count"],
            "last_recorded_at": record["last_recorded_at"].isoformat(),
        }
        for record in aggregates
    ]

    return {"ledger": payload}
