"""In-memory store for analytics events."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from statistics import fmean
from typing import Any

from ..core.config import get_settings
from services.common.config.base_settings import resolve_env


@dataclass
class CapsuleRun:
    capsule_id: str
    tenant_id: str
    persona: str
    success: bool
    tokens: int
    revisions: int
    duration_seconds: float
    recorded_at: datetime


    @dataclass
    class PersonaRegression:
    persona_id: str
    tenant_id: str
    last_run_at: datetime | None = None
    status: str = "pending"
    notes: list[str] = field(default_factory=list)
    queued_at: datetime | None = None
    running_at: datetime | None = None
    last_error: str | None = None


    @dataclass
    class GovernanceReport:
        report_id: str
        tenant_id: str
        generated_at: datetime
        summary: str
        changes: list[str]


        @dataclass
        class KamachiqRun:
            run_id: str
            tenant_id: str
            name: str
            deliverable_count: int
            created_at: datetime
            metadata: dict[str, str] = field(default_factory=dict)


            @dataclass
            class BillingEvent:
                event_id: str
                tenant_id: str
                service: str
                cost: float
                currency: str
                recorded_at: datetime
                capsule_id: str | None = None
                tokens: int = 0
                metadata: dict[str, str] = field(default_factory=dict)


                @dataclass
                class DisasterRecoveryDrill:
                    drill_id: str
                    primary_region: str
                    failover_region: str
                    started_at: datetime
                    ended_at: datetime
                    rto_seconds: float
                    rpo_seconds: float
                    succeeded: bool
                    notes: str | None = None


                    @dataclass
                    class BenchmarkResult:
                        benchmark_id: str
                        suite: str
                        scenario: str
                        service: str
                        target: str
                        started_at: datetime
                        completed_at: datetime
                        score: float
                        metrics: dict[str, float] = field(default_factory=dict)
                        metadata: dict[str, str] = field(default_factory=dict)
                        tenant_id: str | None = None


                        class AnalyticsStore:
                            """Simple in-memory analytics store."""

    def __init__(self) -> None:
        self.runs: deque[CapsuleRun] = deque(maxlen=1000)
        self.regressions: dict[str, PersonaRegression] = {}
        self.governance_reports: deque[GovernanceReport] = deque(maxlen=200)
        self.notifications: list[dict[str, str]] = []
        self.kamachiq_runs: deque[KamachiqRun] = deque(maxlen=200)
        self.blocked_deliverables: deque[dict[str, str]] = deque(maxlen=200)
        self.resolved_deliverables: deque[dict[str, str]] = deque(maxlen=200)
        self.billing_events: deque[BillingEvent] = deque(maxlen=5000)
        self.drills: deque[DisasterRecoveryDrill] = deque(maxlen=200)
        self.benchmarks: deque[BenchmarkResult] = deque(maxlen=500)

    def record_run(self, run: CapsuleRun) -> None:
        self.runs.append(run)

    def register_regression(self, persona_id: str, tenant_id: str) -> PersonaRegression:
        key = self._persona_key(persona_id, tenant_id)
        regression = self.regressions.get(key)
        if regression is None:
    regression = PersonaRegression(persona_id=persona_id, tenant_id=tenant_id)
    self.regressions[key] = regression
    return regression

    def transition_regression(
    self,
    persona_id: str,
    tenant_id: str,
    status: str,
    *,
    note: str | None = None,
    error: str | None = None,
    ) -> PersonaRegression:
    regression = self.register_regression(persona_id, tenant_id)
    now = datetime.now(UTC)
    regression.status = status
    if status == "queued":
        regression.queued_at = now
        elif status == "running":
            regression.running_at = now
            elif status == "completed":
                regression.last_run_at = now
                regression.last_error = None
                elif status == "failed":
                    regression.last_error = error or note
                    regression.last_run_at = now

                    if note:
                        regression.notes.append(note)
                        return regression

    def store_governance_report(self, report: GovernanceReport) -> None:
        self.governance_reports.append(report)

    def list_regressions(self) -> list[PersonaRegression]:
        return list(self.regressions.values())

    def list_runs(self) -> list[CapsuleRun]:
        return list(self.runs)

    def list_reports(self, tenant_id: str | None = None) -> list[GovernanceReport]:
        if tenant_id:
    return [r for r in self.governance_reports if r.tenant_id == tenant_id]
    return list(self.governance_reports)

    def log_notification(self, tenant_id: str, message: str) -> None:
        self.notifications.append(
        {
        "tenant_id": tenant_id,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
        }
        )

    def record_kamachiq_run(self, run: KamachiqRun) -> None:
        self.kamachiq_runs.append(run)

    def list_kamachiq_runs(self, tenant_id: str | None = None) -> list[KamachiqRun]:
        if tenant_id:
    return [r for r in self.kamachiq_runs if r.tenant_id == tenant_id]
    return list(self.kamachiq_runs)

    def kamachiq_summary(self) -> dict[str, Any]:
        runs = self.list_kamachiq_runs()
        if not runs:
    return {"count": 0, "average_deliverables": 0.0, "tenants": []}
    total_deliverables = sum(
    int(run.metadata.get("deliverable_count", run.deliverable_count))
    for run in runs
    )
    tenants = sorted(set(run.tenant_id for run in runs))
    return {
    "count": len(runs),
    "average_deliverables": total_deliverables / len(runs),
    "tenants": tenants,
    "last_run": max(runs, key=lambda r: r.created_at).__dict__,
    }

    def record_billing_event(self, event: BillingEvent) -> None:
        self.billing_events.append(event)

    def list_billing_events(self, tenant_id: str | None = None) -> list[BillingEvent]:
        if tenant_id:
    return [e for e in self.billing_events if e.tenant_id == tenant_id]
    return list(self.billing_events)

    def aggregate_billing(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
                                                                                                                                aggregates: dict[tuple[str, str | None, str, str], dict[str, Any]] = {}
                                                                                                                                for event in self.list_billing_events(tenant_id):
                                                                                                                                    key = (event.tenant_id, event.capsule_id, event.service, event.currency)
                                                                                                                                    entry = aggregates.setdefault(
                                                                                                                                    key,
                                                                                                                                    {
                                                                                                                                    "tenant_id": event.tenant_id,
                                                                                                                                    "capsule_id": event.capsule_id,
                                                                                                                                    "service": event.service,
                                                                                                                                    "currency": event.currency,
                                                                                                                                    "total_tokens": 0,
                                                                                                                                    "total_cost": 0.0,
                                                                                                                                    "event_count": 0,
                                                                                                                                    "last_recorded_at": event.recorded_at,
                                                                                                                                    },
                                                                                                                                    )
                                                                                                                                    entry["total_tokens"] += event.tokens
                                                                                                                                    entry["total_cost"] += event.cost
                                                                                                                                    entry["event_count"] += 1
                                                                                                                                    if event.recorded_at > entry["last_recorded_at"]:
    entry["last_recorded_at"] = event.recorded_at
    return list(aggregates.values())

    def record_blocked_deliverable(self, data: dict[str, str]) -> None:
        self.blocked_deliverables.append(data)

    def list_blocked_deliverables(
    self, tenant_id: str | None = None
    ) -> list[dict[str, str]]:
    if tenant_id:
        return [
        d for d in self.blocked_deliverables if d.get("tenant_id") == tenant_id
        ]
        return list(self.blocked_deliverables)

    def record_resolved_deliverable(self, data: dict[str, str]) -> None:
        self.resolved_deliverables.append(data)

    def list_resolved_deliverables(
    self, tenant_id: str | None = None
    ) -> list[dict[str, str]]:
    if tenant_id:
        return [
        d for d in self.resolved_deliverables if d.get("tenant_id") == tenant_id
        ]
        return list(self.resolved_deliverables)

    def pending_regressions(
                            self, now: datetime | None = None
                            ) -> list[PersonaRegression]:
                                settings = get_settings()
                                now = now or datetime.now(UTC)
                                due: list[PersonaRegression] = []
                                for regression in self.regressions.values():
                                    if regression.status in {"queued", "running"}:
                                        continue
                                        if regression.status == "failed":
                                            due.append(regression)
                                            continue
                                            if regression.last_run_at is None:
                                                due.append(regression)
                                                else:
                                                    delta = now - regression.last_run_at
                                                    if delta >= timedelta(hours=settings.regression_interval_hours):
                                                        due.append(regression)
                                                        return due

    def record_drill(self, drill: DisasterRecoveryDrill) -> None:
        self.drills.append(drill)

    def list_drills(self) -> list[DisasterRecoveryDrill]:
        return list(self.drills)

    def drill_summary(self) -> dict[str, Any]:
        drills = self.list_drills()
        if not drills:
    return {
    "count": 0,
    "average_rto_seconds": 0.0,
    "average_rpo_seconds": 0.0,
    "last_drill": None,
    "success_rate": 0.0,
    }
    total_rto = sum(drill.rto_seconds for drill in drills)
    total_rpo = sum(drill.rpo_seconds for drill in drills)
    successes = sum(1 for drill in drills if drill.succeeded)
    last_drill = max(drills, key=lambda d: d.ended_at)
    return {
    "count": len(drills),
    "average_rto_seconds": total_rto / len(drills),
    "average_rpo_seconds": total_rpo / len(drills),
    "last_drill": last_drill.__dict__,
    "success_rate": successes / len(drills),
    }

    def record_benchmark(self, result: BenchmarkResult) -> None:
        self.benchmarks.append(result)

    def list_benchmarks(
    self,
    suite: str | None = None,
    scenario: str | None = None,
    tenant_id: str | None = None,
    ) -> list[BenchmarkResult]:
    results = list(self.benchmarks)
    if suite:
        results = [item for item in results if item.suite == suite]
        if scenario:
            results = [item for item in results if item.scenario == scenario]
            if tenant_id:
                results = [item for item in results if item.tenant_id == tenant_id]
                return results

    def latest_benchmarks(self, limit: int = 20) -> list[BenchmarkResult]:
        return list(self.benchmarks)[-limit:]

    def benchmark_scoreboard(
                                        self,
                                        suite: str | None = None,
                                        tenant_id: str | None = None,
                                        ) -> list[dict[str, Any]]:
                                            results = self.list_benchmarks(suite=suite, tenant_id=tenant_id)
                                            if not results:
                                                return []

                                                by_scenario: dict[str, list[BenchmarkResult]] = defaultdict(list)
                                                for result in results:
                                                    by_scenario[result.scenario].append(result)

                                                    scoreboard: list[dict[str, Any]] = []
                                                    for scenario, items in by_scenario.items():
                                                        best = max(items, key=lambda item: item.score)
                                                        avg_latency = self._avg_metric(items, "latency_p95_ms")
                                                        avg_throughput = self._avg_metric(items, "requests_per_second")
                                                        avg_error_rate = self._avg_metric(items, "error_rate")
                                                        scoreboard.append(
                                                        {
                                                        "scenario": scenario,
                                                        "attempts": len(items),
                                                        "best_service": best.service,
                                                        "best_score": best.score,
                                                        "best_benchmark_id": best.benchmark_id,
                                                        "average_latency_p95_ms": avg_latency,
                                                        "average_requests_per_second": avg_throughput,
                                                        "average_error_rate": avg_error_rate,
                                                        }
                                                        )

                                                        scoreboard.sort(key=lambda entry: entry["best_score"], reverse=True)
                                                        return scoreboard

                                                        @staticmethod
    def _avg_metric(items: list[BenchmarkResult], metric: str) -> float:
        values = [
        item.metrics.get(metric)
        for item in items
        if item.metrics.get(metric) is not None
        ]
        if not values:
    return 0.0
    return round(fmean(values), 4)

    @staticmethod
    def _persona_key(persona_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{persona_id}"


        store = AnalyticsStore()
