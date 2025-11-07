"""Temporal workflow for executing a capsule.

The roadmap (ROADMAP‑2.5.md) defines a *capsule‑run* endpoint that should
trigger a Temporal workflow which ultimately launches the capsule steps in
isolated containers (or Kubernetes Jobs).  The existing codebase only contains
the endpoint (`/capsule/run`) but no workflow implementation.  This file adds a
minimal, production‑ready workflow that satisfies the roadmap's **core
functionality** while leaving room for future extension (e.g., Docker/K8s job
launch, policy checks, result aggregation).

The workflow:
1. Receives a :class:`CapsuleRunInput` data class (matching the JSON schema
   expected by the API).
2. Logs the start of the run via Temporal's logger.
3. Executes a single activity ``execute_capsule`` which, for now, simply logs
   the execution and returns a success string.  In a later sprint this activity
   will be expanded to launch the actual container / job and stream logs.
4. Returns the activity result – a short human‑readable message that the
   orchestrator can forward to the caller.

Both the workflow and activity are defined using the ``temporalio`` decorators
so they are automatically discoverable by the Temporal worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow
from services.common.observability import get_meter, get_tracer
import subprocess
from prometheus_client import Counter

# ---------------------------------------------------------------------------
# Input model
# ---------------------------------------------------------------------------

@dataclass
class CapsuleRunInput:
    """Input payload for a capsule run.

    The fields correspond exactly to the JSON body accepted by the gateway
    ``/capsules/{capsule_id}/{version}/run`` endpoint (see
    ``services/gateway-api/app/api/capsules.py``).  Keeping the dataclass in a
    shared module ensures type‑safety across the API layer and the Temporal
    worker.
    """

    run_id: str
    capsule_id: str
    version: str
    tenant: str
    user: str
    params: Dict[str, Any]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Observability primitives for the capsule workflow
# ---------------------------------------------------------------------------
_capsule_meter = get_meter("capsule_workflow")
_capsule_counter = _capsule_meter.create_counter(
    name="capsule_workflow_runs_total",
    description="Total number of capsule workflow executions",
)
_capsule_histogram = _capsule_meter.create_histogram(
    name="capsule_workflow_duration_seconds",
    description="Duration of capsule workflow runs",
)

_tracer = get_tracer("capsule_workflow")

@workflow.defn(name="capsule-run-workflow")
class CapsuleRunWorkflow:
    """Temporal workflow that orchestrates a single capsule execution.

    The workflow is intentionally lightweight for the initial implementation –
    it delegates the heavy lifting to the ``execute_capsule`` activity.  Future
    iterations can add additional activities (e.g., policy checks, result
    persistence, audit logging) without changing the public contract.
    """

    @workflow.run
    async def run(self, payload: CapsuleRunInput) -> str:
        # Increment the total run counter.
        _capsule_counter.add(1, {
            "capsule": payload.capsule_id,
            "version": payload.version,
            "tenant": payload.tenant,
        })

        # Start a span for the whole workflow execution.
        with _tracer.start_as_current_span("capsule_run_workflow") as span:
            span.set_attribute("capsule.id", payload.capsule_id)
            span.set_attribute("capsule.version", payload.version)
            span.set_attribute("run.id", payload.run_id)
            span.set_attribute("tenant", payload.tenant)
            span.set_attribute("user", payload.user)

            workflow.logger.info(
                "Capsule run started",
                extra={
                    "capsule": payload.capsule_id,
                    "version": payload.version,
                    "run_id": payload.run_id,
                    "tenant": payload.tenant,
                    "user": payload.user,
                },
            )

            # Execute the capsule via an activity.  A generous timeout is provided
            # because real capsule workloads can be long‑running.
            result = await workflow.execute_activity(
                execute_capsule,
                payload,
                start_to_close_timeout=timedelta(minutes=30),
            )

            workflow.logger.info(
                "Capsule run completed",
                extra={"run_id": payload.run_id, "result": result},
            )

            # Record duration histogram (using workflow execution time).
            # Temporal does not expose elapsed time directly; we rely on the span
            # duration which the exporter will capture.  For explicit metric we
            # could compute using timestamps, but the span provides sufficient
            # granularity for most observability stacks.
            return result


# ---------------------------------------------------------------------------
# Activity implementation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Activity observability – each execution is traced and counted.
# ---------------------------------------------------------------------------
_activity_meter = get_meter("capsule_activity")
_activity_counter = _activity_meter.create_counter(
    name="capsule_activity_executions_total",
    description="Total number of capsule activity executions",
)
_activity_tracer = get_tracer("capsule_activity")

@activity.defn(name="execute_capsule")
async def execute_capsule(payload: CapsuleRunInput) -> str:
    """Execute a capsule using a Docker container.

    The activity expects ``payload.params`` to contain at least an ``image`` key
    (Docker image name).  An optional ``command`` key can be either a string or a
    list of arguments.  If ``command`` is omitted the container will run its
    default entrypoint.

    The implementation uses ``subprocess.run`` with ``docker`` CLI to keep the
    dependency surface minimal – the host environment (CI / dev cluster) already
    provides the Docker daemon.  Errors are captured and re‑raised so that the
    Temporal workflow records a failure.
    """
    # Increment Prometheus counter for observability.
    CAPSULE_EXECUTIONS = Counter("capsule_executions_total", "Total capsule executions")
    CAPSULE_EXECUTIONS.inc()

    image: str = payload.params.get("image", "alpine")
    cmd = payload.params.get("command")

    # Build the docker run command.
    docker_cmd = ["docker", "run", "--rm", image]
    if cmd:
        if isinstance(cmd, str):
            docker_cmd.extend(["sh", "-c", cmd])
        elif isinstance(cmd, list):
            docker_cmd.extend(cmd)
        else:
            raise ValueError("payload.params.command must be a string or list of strings")

    # Increment activity counter
    _activity_counter.add(1, {
        "capsule": payload.capsule_id,
        "version": payload.version,
    })

    # Start a span for the activity execution.
    with _activity_tracer.start_as_current_span("execute_capsule_activity") as span:
        span.set_attribute("capsule.id", payload.capsule_id)
        span.set_attribute("capsule.version", payload.version)
        span.set_attribute("run.id", payload.run_id)
        span.set_attribute("tenant", payload.tenant)
        span.set_attribute("user", payload.user)

        activity.logger.info(
            "Running Docker command for capsule",
            extra={
                "capsule": payload.capsule_id,
                "version": payload.version,
                "run_id": payload.run_id,
                "docker_cmd": docker_cmd,
            },
        )

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        activity.logger.error(
            "Docker execution failed",
            extra={"returncode": exc.returncode, "stderr": exc.stderr},
        )
        raise
    except Exception as exc:
        activity.logger.error("Unexpected error during Docker run", extra={"error": str(exc)})
        raise

    activity.logger.info(
        "Docker execution completed",
        extra={"stdout": result.stdout[:200]},
    )

    return (
        f"Capsule {payload.capsule_id}:{payload.version} "
        f"run {payload.run_id} completed with output: {result.stdout.strip()}"
    )
