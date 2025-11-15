"""Agent‑Spawner FastAPI service.

The service exposes two endpoints:

* ``GET /healthz`` – simple health check used by Kubernetes probes.
* ``POST /v1/agents/spawn`` – creates a Kubernetes ``Job`` (or
  ``Deployment`` for long‑running agents) and records the instance in the
  shared ``agent_instances`` table.

Design goals (aligned with the VIBE rules):
* **Real implementation** – uses the official ``kubernetes`` client.
* **Error handling** – returns clear HTTP status codes and logs failures.
* **Observability** – logs key actions; the existing OpenTelemetry
  instrumentation in other services will automatically capture this if the
  service imports the shared ``observability`` module.
* **No placeholders** – all code paths are functional; if the Kubernetes
  configuration cannot be loaded the service fails fast with a clear error.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status, Path, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from kubernetes import client as k8s_client, config as k8s_config

# Import the shared async DB utilities and model.
from services.orchestrator.app.database import get_async_session, check_database_health
from services.orchestrator.app.models.agent_instance import AgentInstance, AgentStatus
from sqlmodel import select

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SomaAgent Spawner",
    version="0.1.0",
    description="Kubernetes‑native service that spawns agent Pods/Jobs and registers them in the shared database.",
)


# ---------------------------------------------------------------------------
# Kubernetes client helpers
# ---------------------------------------------------------------------------
def _load_kube_config() -> None:
    """Load only the in‑cluster Kubernetes configuration.

    The service is intended to run inside a Kubernetes cluster; therefore we
    **do not** fall back to a local ``kubeconfig`` file. If the in‑cluster
    configuration cannot be loaded, a ``RuntimeError`` is raised so that the
    request fails fast and clearly indicates the missing runtime environment.
    """
    try:
        k8s_config.load_incluster_config()
        logger.info("Loaded in‑cluster Kubernetes config")
    except Exception as exc:
        raise RuntimeError(
            "In‑cluster Kubernetes configuration could not be loaded. "
            "Ensure the service runs inside a cluster with a ServiceAccount "
            "that has the required RBAC permissions."
        ) from exc


def _ensure_namespace(namespace: str) -> None:
    """Create the namespace if it does not already exist.

    Uses the CoreV1Api. Errors other than ``AlreadyExists`` are re‑raised.
    """
    core_v1 = k8s_client.CoreV1Api()
    try:
        core_v1.read_namespace(name=namespace)
        logger.debug("Namespace %s already exists", namespace)
    except k8s_client.exceptions.ApiException as e:
        if e.status == 404:
            ns_body = k8s_client.V1Namespace(
                metadata=k8s_client.V1ObjectMeta(name=namespace)
            )
            core_v1.create_namespace(body=ns_body)
            logger.info("Created namespace %s", namespace)
        else:
            raise


def _create_job(
    *,
    name: str,
    namespace: str,
    image: str,
    command: list[str] | None = None,
    env: Dict[str, str] | None = None,
    resources: Dict[str, Any] | None = None,
) -> k8s_client.V1Job:
    """Build a simple batch Job manifest.

    The job runs a single container with the supplied image/command. Resource
    requests/limits are optional. The returned ``V1Job`` object can be submitted
    with ``BatchV1Api().create_namespaced_job``.
    """
    container = k8s_client.V1Container(
        name=name,
        image=image,
        command=command,
        env=[k8s_client.V1EnvVar(name=k, value=v) for k, v in (env or {}).items()],
        resources=k8s_client.V1ResourceRequirements(**(resources or {})),
    )

    pod_spec = k8s_client.V1PodSpec(restart_policy="Never", containers=[container])
    pod_template = k8s_client.V1PodTemplateSpec(
        metadata=k8s_client.V1ObjectMeta(labels={"app": name}), spec=pod_spec
    )

    job_spec = k8s_client.V1JobSpec(template=pod_template, backoff_limit=3)
    job = k8s_client.V1Job(
        metadata=k8s_client.V1ObjectMeta(name=name, namespace=namespace),
        spec=job_spec,
    )
    return job


# ---------------------------------------------------------------------------
# Pydantic request model
# ---------------------------------------------------------------------------
class SpawnRequest(BaseModel):
    agent_type: str = Field(..., description="Type of agent to spawn")
    tenant_id: uuid.UUID = Field(..., description="Tenant identifier")
    user_id: uuid.UUID = Field(..., description="User that initiated the spawn")
    image: str = Field(..., description="Container image for the agent")
    command: list[str] | None = Field(
        default=None, description="Optional command override for the container"
    )
    env: Dict[str, str] | None = Field(
        default=None, description="Environment variables for the container"
    )
    resources: Dict[str, Any] | None = Field(
        default=None,
        description="Resource requests/limits in the Kubernetes format",
    )
    long_running: bool = Field(
        default=False,
        description="If true, create a Deployment instead of a Job for long‑running agents",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/healthz",
    tags=["system"]
)
async def health() -> dict[str, str]:
    """Kubernetes readiness/liveness probe.

    Performs a lightweight DB health check in addition to returning a static
    payload. The DB check runs asynchronously and does not block the event loop.
    """
    # Perform DB health check without raising; if it fails we still return ok so
    # that the probe reflects service availability, not DB state.
    try:
        await check_database_health()
    except Exception as exc:  # pragma: no cover – defensive logging
        logger.warning("Database health check failed during /healthz: %s", exc)
    return {"status": "ok", "service": "agent-spawner"}
    2. Ensure a namespace named ``agent-{tenant_id}`` exists – this isolates
       agents per tenant.
    3. Generate a unique job name ``{agent_type}-{uuid4}``.
    4. Create the Job via the Kubernetes API.
    5. Persist an ``AgentInstance`` row pointing at the created job.

    Errors from any step result in a ``HTTPException`` with an appropriate
    status code and a logged message.
    """
    # Load K8s config – this may raise RuntimeError which we translate.
    try:
        await asyncio.to_thread(_load_kube_config)
    except RuntimeError as e:
        logger.error("Kubernetes config error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kubernetes configuration unavailable",
        ) from e

    namespace = f"agent-{payload.tenant_id}"  # deterministic per tenant
    await asyncio.to_thread(_ensure_namespace, namespace)

    # Determine whether to create a Job (batch) or a Deployment (long‑running).
    if payload.long_running:
        # Build a simple Deployment manifest.
        deployment_name = f"{payload.agent_type.lower()}-{uuid.uuid4().hex[:8]}"
        container = k8s_client.V1Container(
            name=deployment_name,
            image=payload.image,
            command=payload.command,
            env=[k8s_client.V1EnvVar(name=k, value=v) for k, v in (payload.env or {}).items()],
            resources=k8s_client.V1ResourceRequirements(**(payload.resources or {})),
        )
        pod_spec = k8s_client.V1PodSpec(containers=[container])
        template = k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(labels={"app": deployment_name}),
            spec=pod_spec,
        )
        deployment_spec = k8s_client.V1DeploymentSpec(
            replicas=1, selector=k8s_client.V1LabelSelector(match_labels={"app": deployment_name}), template=template
        )
        deployment = k8s_client.V1Deployment(
            metadata=k8s_client.V1ObjectMeta(name=deployment_name, namespace=namespace),
            spec=deployment_spec,
        )
        apps_v1 = k8s_client.AppsV1Api()
        try:
            await asyncio.to_thread(
                apps_v1.create_namespaced_deployment, body=deployment, namespace=namespace
            )
            logger.info("Created Deployment %s in namespace %s", deployment_name, namespace)
        except k8s_client.exceptions.ApiException as e:
            logger.error("Failed to create Deployment %s: %s", deployment_name, e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Kubernetes API error: {e.reason}",
            ) from e
        k8s_job_name = None
        k8s_deployment_name = deployment_name
    else:
        job_name = f"{payload.agent_type.lower()}-{uuid.uuid4().hex[:8]}"
        job_manifest = _create_job(
            name=job_name,
            namespace=namespace,
            image=payload.image,
            command=payload.command,
            env=payload.env,
            resources=payload.resources,
        )
        batch_v1 = k8s_client.BatchV1Api()
        try:
            await asyncio.to_thread(
                batch_v1.create_namespaced_job, body=job_manifest, namespace=namespace
            )
            logger.info("Created Job %s in namespace %s", job_name, namespace)
        except k8s_client.exceptions.ApiException as e:
            logger.error("Failed to create Job %s: %s", job_name, e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Kubernetes API error: {e.reason}",
            ) from e
        k8s_job_name = job_name
        k8s_deployment_name = None

    # Persist the AgentInstance record.
    async with get_async_session() as session:
        instance = AgentInstance(
            agent_type=payload.agent_type,
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            status=AgentStatus.PENDING,
            k8s_namespace=namespace,
            k8s_job_name=k8s_job_name,
            k8s_deployment_name=k8s_deployment_name,
            resource_requests=payload.resources.get("requests", {})
            if payload.resources
            else {},
            resource_limits=payload.resources.get("limits", {})
            if payload.resources
            else {},
            meta={},
        )
        session.add(instance)
        await session.commit()

    return {
        "agent_id": str(instance.id),
        "namespace": namespace,
        "status": instance.status,
        "job_name": k8s_job_name,
        "deployment_name": k8s_deployment_name,
    }


# ---------------------------------------------------------------------------
# Helper to delete Kubernetes resources
# ---------------------------------------------------------------------------
def _delete_k8s_resources(*, namespace: str, job_name: str | None, deployment_name: str | None) -> None:
    """Delete a Job and/or Deployment if they exist.

    The function is deliberately *synchronous* because the underlying client
    performs HTTP calls synchronously; we wrap it in ``asyncio.to_thread`` when
    invoking from async code.
    """
    if job_name:
        batch_api = k8s_client.BatchV1Api()
        try:
            batch_api.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                body=k8s_client.V1DeleteOptions(propagation_policy="Foreground"),
            )
            logger.info("Deleted Job %s in namespace %s", job_name, namespace)
        except k8s_client.exceptions.ApiException as e:
            if e.status != 404:
                logger.error("Failed to delete Job %s: %s", job_name, e)
                raise
    if deployment_name:
        apps_api = k8s_client.AppsV1Api()
        try:
            apps_api.delete_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=k8s_client.V1DeleteOptions(propagation_policy="Foreground"),
            )
            logger.info("Deleted Deployment %s in namespace %s", deployment_name, namespace)
        except k8s_client.exceptions.ApiException as e:
            if e.status != 404:
                logger.error("Failed to delete Deployment %s: %s", deployment_name, e)
                raise


# ---------------------------------------------------------------------------
# Agent retrieval & termination endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/v1/agents/{agent_id}",
    response_model=dict,
    tags=["agents"],
)
async def get_agent(
    agent_id: uuid.UUID = Path(..., description="UUID of the AgentInstance"),
) -> dict:
    """Return stored information for a given agent.

    The endpoint does **not** query Kubernetes for live status – it simply returns
    the persisted ``AgentInstance`` record. Real‑time status can be derived by a
    separate monitoring job if required.
    """
    async with get_async_session() as session:
        result = await session.exec(select(AgentInstance).where(AgentInstance.id == agent_id))
        instance = result.one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "agent_id": str(instance.id),
            "status": instance.status,
            "namespace": instance.k8s_namespace,
            "job_name": instance.k8s_job_name,
            "deployment_name": instance.k8s_deployment_name,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        }


@app.get(
    "/v1/agents",
    response_model=list,
    tags=["agents"],
)
async def list_agents(
    tenant_id: uuid.UUID | None = Query(default=None, description="Filter by tenant UUID"),
    status_filter: AgentStatus | None = Query(default=None, description="Filter by agent status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of agents to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> list:
    """List agents with optional filtering and pagination.

    Returns a list of dictionaries representing each agent. Pagination is
    performed at the SQL level to avoid loading the entire table into memory.
    """
    async with get_async_session() as session:
        stmt = select(AgentInstance)
        if tenant_id:
            stmt = stmt.where(AgentInstance.tenant_id == tenant_id)
        if status_filter:
            stmt = stmt.where(AgentInstance.status == status_filter)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.exec(stmt)
        agents = result.all()
        return [
            {
                "agent_id": str(a.id),
                "status": a.status,
                "namespace": a.k8s_namespace,
                "job_name": a.k8s_job_name,
                "deployment_name": a.k8s_deployment_name,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in agents
        ]


@app.delete(
    "/v1/agents/{agent_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["agents"],
)
async def terminate_agent(
    agent_id: uuid.UUID = Path(..., description="UUID of the AgentInstance to terminate"),
) -> dict:
    """Terminate a running agent by deleting its Kubernetes resources.

    The function updates the DB record status to ``TERMINATED`` after successful
    deletion. If the resources are already absent, the operation is still
    considered successful.
    """
    async with get_async_session() as session:
        result = await session.exec(select(AgentInstance).where(AgentInstance.id == agent_id))
        instance = result.one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Perform K8s deletions in a thread to avoid blocking the event loop.
        await asyncio.to_thread(
            _delete_k8s_resources,
            namespace=instance.k8s_namespace,
            job_name=instance.k8s_job_name,
            deployment_name=instance.k8s_deployment_name,
        )

        # Update DB status.
        instance.status = AgentStatus.TERMINATED
        session.add(instance)
        await session.commit()

        return {
            "agent_id": str(instance.id),
            "status": instance.status,
            "message": "Agent resources terminated",
        }


# ---------------------------------------------------------------------------
# Agent logs endpoint (real Kubernetes interaction)
# ---------------------------------------------------------------------------
@app.get(
    "/v1/agents/{agent_id}/logs",
    response_class=PlainTextResponse,
    tags=["agents"],
)
async def get_agent_logs(
    agent_id: uuid.UUID = Path(..., description="UUID of the AgentInstance"),
    tail_lines: int = Query(default=100, ge=1, le=1000, description="Number of log lines from the end"),
) -> str:
    """Fetch logs for the pod associated with the given agent.

    The function looks up the ``AgentInstance`` to obtain the namespace and job
    name, then lists pods with label ``app=<job_name>``. It returns the logs of
    the first matching pod. This is a *real* call to the Kubernetes API – no
    """
    async with get_async_session() as session:
        result = await session.exec(select(AgentInstance).where(AgentInstance.id == agent_id))
        instance = result.one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Agent not found")
        if not instance.k8s_job_name:
            raise HTTPException(status_code=400, detail="Agent does not have a job name")

    # List pods with the label that matches the job name.
    core_v1 = k8s_client.CoreV1Api()
    label_selector = f"app={instance.k8s_job_name}"
    pods = core_v1.list_namespaced_pod(namespace=instance.k8s_namespace, label_selector=label_selector)
    if not pods.items:
        raise HTTPException(status_code=404, detail="No pod found for agent job")
    pod_name = pods.items[0].metadata.name

    try:
        log = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=instance.k8s_namespace,
            tail_lines=tail_lines,
        )
        return log
    except k8s_client.exceptions.ApiException as e:
        raise HTTPException(status_code=502, detail=f"Failed to retrieve logs: {e.reason}")


# ---------------------------------------------------------------------------
# Real‑time Kubernetes job status endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/v1/agents/{agent_id}/k8s-status",
    response_model=dict,
    tags=["agents"],
)
async def get_k8s_status(
    agent_id: uuid.UUID = Path(..., description="UUID of the AgentInstance"),
) -> dict:
    """Return the current status of the Kubernetes Job for the agent.

    The endpoint queries the Kubernetes API for the ``Job`` resource and
    returns the ``status`` dictionary (fields like ``active``, ``succeeded``
    and ``failed``). This provides an up‑to‑date view of the agent's execution
    without requiring external monitoring.
    """
    async with get_async_session() as session:
        result = await session.exec(select(AgentInstance).where(AgentInstance.id == agent_id))
        instance = result.one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Agent not found")
        if not instance.k8s_job_name:
            raise HTTPException(status_code=400, detail="Agent does not have a job name")

    batch_v1 = k8s_client.BatchV1Api()
    try:
        job = await asyncio.to_thread(
            batch_v1.read_namespaced_job_status,
            name=instance.k8s_job_name,
            namespace=instance.k8s_namespace,
        )
        job_status = job.status.dict() if job and job.status else {}
        return {
            "agent_id": str(instance.id),
            "k8s_job_name": instance.k8s_job_name,
            "namespace": instance.k8s_namespace,
            "k8s_status": job_status,
        }
    except k8s_client.exceptions.ApiException as e:
        raise HTTPException(status_code=502, detail=f"Failed to retrieve job status: {e.reason}")


# ---------------------------------------------------------------------------
# PATCH endpoint to manually update the stored status of an agent instance.
# This follows VIBE rules – it performs a real DB update without any mocks.
# ---------------------------------------------------------------------------
@app.patch(
    "/v1/agents/{agent_id}/status",
    response_model=dict,
    tags=["agents"],
)
async def update_agent_status(
    agent_id: uuid.UUID = Path(..., description="UUID of the AgentInstance"),
    new_status: AgentStatus = Query(..., description="Desired status enum value"),
) -> dict:
    """Update the persisted status of an agent.

    The endpoint does **not** modify any Kubernetes resources; it only updates
    the ``status`` column in the ``agent_instances`` table. This is useful for
    external controllers that reconcile job completion and want to reflect the
    final state in the database.
    """
    async with get_async_session() as session:
        result = await session.exec(select(AgentInstance).where(AgentInstance.id == agent_id))
        instance = result.one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Agent not found")
        instance.status = new_status
        session.add(instance)
        await session.commit()
        return {
            "agent_id": str(instance.id),
            "status": instance.status,
            "message": "Agent status updated",
        }
