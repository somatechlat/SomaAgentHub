"""In-memory store for analytics events."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional

from ..core.config import get_settings


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
    last_run_at: Optional[datetime] = None
    status: str = "pending"
    notes: List[str] = field(default_factory=list)
    queued_at: Optional[datetime] = None
    running_at: Optional[datetime] = None
    last_error: Optional[str] = None


@dataclass
class GovernanceReport:
    report_id: str
    tenant_id: str
    generated_at: datetime
    summary: str
    changes: List[str]


@dataclass
class KamachiqRun:
    run_id: str
    tenant_id: str
    name: str
    deliverable_count: int
    created_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class BillingEvent:
    event_id: str
    tenant_id: str
    service: str
    cost: float
    currency: str
    recorded_at: datetime
    capsule_id: Optional[str] = None
    tokens: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)


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


class AnalyticsStore:
    """Simple in-memory analytics store."""

    def __init__(self) -> None:
        self.runs: Deque[CapsuleRun] = deque(maxlen=1000)
        self.regressions: Dict[str, PersonaRegression] = {}
        self.governance_reports: Deque[GovernanceReport] = deque(maxlen=200)
        self.notifications: List[Dict[str, str]] = []
        self.kamachiq_runs: Deque[KamachiqRun] = deque(maxlen=200)
        self.blocked_deliverables: Deque[Dict[str, str]] = deque(maxlen=200)
        self.resolved_deliverables: Deque[Dict[str, str]] = deque(maxlen=200)
        self.billing_events: Deque[BillingEvent] = deque(maxlen=5000)
        self.drills: Deque[DisasterRecoveryDrill] = deque(maxlen=200)

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
        now = datetime.utcnow()
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

    def list_regressions(self) -> List[PersonaRegression]:
        return list(self.regressions.values())

    def list_runs(self) -> List[CapsuleRun]:
        return list(self.runs)

    def list_reports(self, tenant_id: Optional[str] = None) -> List[GovernanceReport]:
        if tenant_id:
            return [r for r in self.governance_reports if r.tenant_id == tenant_id]
        return list(self.governance_reports)

    def log_notification(self, tenant_id: str, message: str) -> None:
        self.notifications.append({
            "tenant_id": tenant_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def record_kamachiq_run(self, run: KamachiqRun) -> None:
        self.kamachiq_runs.append(run)

    def list_kamachiq_runs(self, tenant_id: Optional[str] = None) -> List[KamachiqRun]:
        if tenant_id:
            return [r for r in self.kamachiq_runs if r.tenant_id == tenant_id]
        return list(self.kamachiq_runs)

    def kamachiq_summary(self) -> Dict[str, Any]:
        runs = self.list_kamachiq_runs()
        if not runs:
            return {"count": 0, "average_deliverables": 0.0, "tenants": []}
        total_deliverables = sum(int(run.metadata.get("deliverable_count", run.deliverable_count)) for run in runs)
        tenants = sorted(set(run.tenant_id for run in runs))
        return {
            "count": len(runs),
            "average_deliverables": total_deliverables / len(runs),
            "tenants": tenants,
            "last_run": max(runs, key=lambda r: r.created_at).__dict__,
        }

    def record_billing_event(self, event: BillingEvent) -> None:
        self.billing_events.append(event)

    def list_billing_events(self, tenant_id: Optional[str] = None) -> List[BillingEvent]:
        if tenant_id:
            return [e for e in self.billing_events if e.tenant_id == tenant_id]
        return list(self.billing_events)

    def aggregate_billing(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        aggregates: Dict[tuple[str, Optional[str], str, str], Dict[str, Any]] = {}
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

    def record_blocked_deliverable(self, data: Dict[str, str]) -> None:
        self.blocked_deliverables.append(data)

    def list_blocked_deliverables(self, tenant_id: Optional[str] = None) -> List[Dict[str, str]]:
        if tenant_id:
            return [d for d in self.blocked_deliverables if d.get("tenant_id") == tenant_id]
        return list(self.blocked_deliverables)

    def record_resolved_deliverable(self, data: Dict[str, str]) -> None:
        self.resolved_deliverables.append(data)

    def list_resolved_deliverables(self, tenant_id: Optional[str] = None) -> List[Dict[str, str]]:
        if tenant_id:
            return [d for d in self.resolved_deliverables if d.get("tenant_id") == tenant_id]
        return list(self.resolved_deliverables)

    def pending_regressions(self, now: Optional[datetime] = None) -> List[PersonaRegression]:
        settings = get_settings()
        now = now or datetime.utcnow()
        due: List[PersonaRegression] = []
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

    def list_drills(self) -> List[DisasterRecoveryDrill]:
        return list(self.drills)

    def drill_summary(self) -> Dict[str, Any]:
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

    @staticmethod
    def _persona_key(persona_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{persona_id}"


store = AnalyticsStore()
