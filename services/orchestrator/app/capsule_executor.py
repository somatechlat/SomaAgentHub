"""Capsule executor activity implementation.

This module provides a richer implementation for the ``execute_capsule``
activity used by the ``capsule-run-workflow``.  The original stub executed a
single Docker container based on ``payload.params['image']`` and returned a
string.  The canonical roadmap (see `docs/ROADMAP.md`) requires a *worker* that can:

  1. Resolve a capsule manifest (a YAML document describing one or more steps).
  2. Execute each step in its own Docker container.
  3. Capture any artefacts produced by the step and upload them to the object
     store (MinIO/S3) using the existing ``ObjectStoreClient``.
  4. Return a structured result that can be persisted by the ``memory-gateway``
     service.

For the MVP we keep the implementation lightweight and avoid external
dependencies beyond ``pyyaml`` (already present in the CI environment).  The
activity supports two input styles:

    * **Legacy single‑image mode** – ``payload.params`` contains ``image`` and
      optional ``command`` (the behaviour that existed before this change).
    * **Manifest mode** – ``payload.params`` contains a ``manifest`` key whose
      value is a YAML string or a path to a local file.  The manifest must be a
      list of steps, each step being a mapping with the keys ``image``,
      ``command`` (optional), and ``output_path`` (optional, path inside the
      container that should be uploaded).

The activity returns a ``dict`` with the overall status and a list of uploaded
artefact URLs (if any).  The surrounding workflow will normalise the result
into the ``SessionStatusResponse`` payload.
"""

from __future__ import annotations

import subprocess
import tempfile

# Local lightweight CapsuleRunInput to avoid importing workflow module here
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx  # Added for manifest fetch (ruff F821)
import yaml
from temporalio import activity

from services.common.observability import get_meter, get_tracer
from services.object_store.app.client import ObjectStoreClient, ObjectStoreSettings
from services.orchestrator.app.core.config import (
    settings,
)  # Provides capsule_repo_url


@dataclass
class CapsuleRunInput:
    run_id: str
    capsule_id: str
    version: str
    tenant: str
    user: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Observability primitives for the executor activity
# ---------------------------------------------------------------------------
_executor_meter = get_meter("capsule_executor")
_executor_counter = _executor_meter.create_counter(
    name="capsule_executor_runs_total",
    description="Total number of capsule executor runs",
)
_executor_tracer = get_tracer("capsule_executor")


def _upload_artifact(client: ObjectStoreClient, tenant: str, capsule: str, version: str, local_path: Path) -> str:
    """Upload a file to the object store and return a presigned URL.

    The key layout mirrors the one used by the memory‑gateway when storing
    results: ``{tenant}/{capsule}/{version}/{filename}``.
    """
    # Ensure the bucket exists – the client stub creates it on‑the‑fly.
    bucket = client.settings.bucket_name
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    object_key = f"{tenant}/{capsule}/{version}/{local_path.name}"
    # The client expects a file‑like object; ``Path.open`` returns a buffered
    # reader suitable for the stub implementation.
    with local_path.open("rb") as f:
        client.upload(object_key, f, length=local_path.stat().st_size)
    # Generate a short‑lived presigned URL (default 1 hour).
    return client.presign_get(object_key)


def _run_docker_step(step: dict[str, Any], payload: CapsuleRunInput) -> str:
    """Run a single Docker step and return its stdout.

    ``step`` must contain at least an ``image`` key.  ``command`` may be a
    string or a list of arguments.  ``output_path`` is optional – if provided the
    caller can copy the path from the container after the run.
    """
    image: str = step["image"]
    cmd = step.get("command")
    docker_cmd = ["docker", "run", "--rm", "-i"]
    # Mount a temporary directory so we can extract artefacts.
    with tempfile.TemporaryDirectory() as tmpdir:
        host_tmp = Path(tmpdir)
        # Bind‑mount the temporary directory at /output inside the container.
        docker_cmd.extend(["-v", f"{host_tmp}:/output"])
        docker_cmd.append(image)
        if cmd:
            if isinstance(cmd, str):
                docker_cmd.extend(["sh", "-c", cmd])
            elif isinstance(cmd, list):
                docker_cmd.extend(cmd)
            else:
                raise ValueError("step.command must be string or list")

        activity.logger.info(
            "Executing Docker step",
            extra={"image": image, "docker_cmd": docker_cmd},
        )
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        # If an output_path is defined, copy the file from the temporary dir.
        output_path = step.get("output_path")
        if output_path:
            src = host_tmp / Path(output_path).name
            if src.exists():
                # Return the path so the caller can upload it.
                return str(src)
        return result.stdout.strip()


@activity.defn(name="execute_capsule")
async def execute_capsule(payload: CapsuleRunInput) -> dict[str, Any]:
    """Execute a capsule.

    The activity supports two modes:
        * **Legacy mode** – ``payload.params`` contains ``image`` and optional
          ``command``.  This mirrors the previous implementation and is kept for
          backward compatibility.
        * **Manifest mode** – ``payload.params`` contains a ``manifest`` key.  The
          manifest is a YAML string or a path to a file that describes a list of
          steps.  Each step may produce an artefact that will be uploaded to the
          object store.
    """
    # Record that we started a run.
    _executor_counter.add(1, {"capsule": payload.capsule_id, "version": payload.version})

    # -------------------------------------------------------------------
    # Helper to create the object‑store client – we lazily initialise it only
    # when we actually need to upload something.
    # -------------------------------------------------------------------
    object_store_client: ObjectStoreClient | None = None

    def _ensure_client() -> ObjectStoreClient:
        nonlocal object_store_client
        if object_store_client is None:
            settings = ObjectStoreSettings.from_env()
            object_store_client = ObjectStoreClient(settings)
        return object_store_client

    # -------------------------------------------------------------------
    # Determine which execution mode to use.
    # -------------------------------------------------------------------
    params = payload.params or {}
    steps: list[dict[str, Any]] = []
    # 1️⃣ If a manifest is explicitly provided in the payload, use it.
    if "manifest" in params:
        manifest_src = params["manifest"]
        if isinstance(manifest_src, str) and Path(manifest_src).exists():
            manifest_content = Path(manifest_src).read_text()
        else:
            # Assume it is a raw YAML string.
            manifest_content = str(manifest_src)
        steps = yaml.safe_load(manifest_content) or []
    else:
        # 2️⃣ Otherwise attempt to fetch a manifest from the capsule‑repo service.
        # The orchestrator configuration provides ``settings.capsule_repo_url``.
        repo_url = f"{settings.capsule_repo_url}/{payload.capsule_id}/{payload.version}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(repo_url)
                resp.raise_for_status()
                manifest_content = resp.text
                steps = yaml.safe_load(manifest_content) or []
        except Exception as exc:
            # If fetching fails we fall back to legacy single‑image mode.
            activity.logger.warning(
                "Failed to fetch capsule manifest, falling back to legacy mode",
                extra={"error": str(exc), "url": repo_url},
            )
            steps = []

    if steps:
        artefacts: list[str] = []
        for step in steps:
            with _executor_tracer.start_as_current_span("capsule_step") as span:
                span.set_attribute("capsule.id", payload.capsule_id)
                span.set_attribute("step.image", step.get("image", ""))
                output_path = step.get("output_path")
                result = _run_docker_step(step, payload)
                if output_path:
                    # ``result`` is the host path of the artefact.
                    client = _ensure_client()
                    url = _upload_artifact(
                        client,
                        payload.tenant,
                        payload.capsule_id,
                        payload.version,
                        Path(result),
                    )
                    artefacts.append(url)
        return {"status": "completed", "artifacts": artefacts}
    else:
        # Legacy single‑image mode – keep the original behaviour.
        image: str = params.get("image", "alpine")
        cmd = params.get("command")
        docker_cmd = ["docker", "run", "--rm", image]
        if cmd:
            if isinstance(cmd, str):
                docker_cmd.extend(["sh", "-c", cmd])
            elif isinstance(cmd, list):
                docker_cmd.extend(cmd)
            else:
                raise ValueError("payload.params.command must be a string or list of strings")

        activity.logger.info(
            "Running Docker command for capsule (legacy mode)",
            extra={"docker_cmd": docker_cmd},
        )
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        return {
            "status": "completed",
            "output": result.stdout.strip(),
        }
