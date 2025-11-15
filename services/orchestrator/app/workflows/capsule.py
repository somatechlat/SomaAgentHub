"""Minimal capsule run workflow for SomaAgentHub.

This starter workflow records its input and returns a trivial result. Future
iterations will integrate resource provisioning, streaming logs, audit trails,
and artifact persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from temporalio import activity, workflow
from services.common.config.base_settings import resolve_env


@dataclass
class CapsuleRunInput:
    """Input payload for a capsule run."""

    run_id: str
    capsule_id: str
    version: str
    tenant: str
    user: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
@dataclass
class CapsuleRunResult:
run_id: str
capsule_id: str
version: str
tenant: str
user: str
status: str
started_at: datetime
completed_at: datetime
params: dict[str, Any]
metadata: dict[str, Any]
summary: str


@activity.defn(name="capsule-generate-summary")
def generate_summary(capsule_id: str, version: str, params: dict[str, Any]) -> str:
"""Produce a deterministic summary of the run parameters.

This keeps the workflow fully executable while still
exercising activity scheduling and result retrieval.
"""
ordered_keys = sorted(params.keys())
kv = ", ".join(f"{k}={params[k]!r}" for k in ordered_keys)
return f"Capsule {capsule_id}@{version} executed with params: {kv or 'none'}"


@workflow.defn(name="capsule-run-workflow")
class CapsuleRunWorkflow:
@workflow.run
async def run(self, payload: CapsuleRunInput) -> CapsuleRunResult:  # noqa: D401
logger = workflow.logger
logger.info("Starting capsule run", payload=payload.__dict__)

started = datetime.now(UTC)
summary = await workflow.execute_activity(
generate_summary,
payload.capsule_id,
payload.version,
payload.params,
start_to_close_timeout=timedelta(seconds=15),
)
result = CapsuleRunResult(
run_id=payload.run_id,
capsule_id=payload.capsule_id,
version=payload.version,
tenant=payload.tenant,
user=payload.user,
status="completed",
started_at=started,
completed_at=datetime.now(UTC),
params=payload.params,
metadata=payload.metadata,
summary=summary,
)
logger.info("Capsule run completed", result=result.__dict__)
return result
