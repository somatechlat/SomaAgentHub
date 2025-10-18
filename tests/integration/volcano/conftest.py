from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_BINARIES = ("kind", "kubectl", "helm")


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    """Execute *command* ensuring failures raise immediately."""

    subprocess.run(command, check=True, env=env)


def _ensure_namespace(namespace: str, env: dict[str, str]) -> None:
    """Create *namespace* if it does not already exist."""

    result = subprocess.run(
        ["kubectl", "get", "namespace", namespace],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _run(["kubectl", "create", "namespace", namespace], env=env)


def _apply_queue_manifests(env: dict[str, str]) -> None:
    """Apply the local queue definitions used by the integration tests."""

    manifest = REPO_ROOT / "infra" / "k8s" / "local" / "volcano" / "queues.yaml"
    _run(["kubectl", "apply", "-f", str(manifest)], env=env)


def _wait_for_queue_ready(queue_name: str, env: dict[str, str]) -> None:
    """Poll Volcano Queue state until it reports Open or timeout reached."""

    deadline = time.time() + 60
    while time.time() < deadline:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "queue",
                queue_name,
                "-o",
                "jsonpath={.status.state}",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            state = result.stdout.strip().lower()
            if state in {"open", "closing"}:
                return
        time.sleep(2)
    raise RuntimeError(f"Volcano queue '{queue_name}' did not become ready within 60s")


@pytest.fixture(scope="module")
def volcano_sandbox() -> dict[str, str]:
    """
    Provision (or reuse) a local Volcano sandbox suitable for end-to-end tests.

    Requires VOLCANO_INTEGRATION_ENABLED environment flag plus kind/kubectl/helm binaries.
    """

    flag = os.environ.get("VOLCANO_INTEGRATION_ENABLED", "")
    if flag.lower() not in {"1", "true", "yes"}:
        pytest.skip("Set VOLCANO_INTEGRATION_ENABLED=1 to run Volcano integration tests.")

    missing = [binary for binary in REQUIRED_BINARIES if shutil.which(binary) is None]
    if missing:
        pytest.skip(
            f"Missing required tools for Volcano integration tests: {', '.join(missing)}"
        )

    env = os.environ.copy()
    cluster_name = (
        env.get("VOLCANO_CLUSTER_NAME")
        or env.get("CLUSTER_NAME")
        or "soma-volcano"
    )
    env["CLUSTER_NAME"] = cluster_name
    env.setdefault("NAMESPACE", env.get("VOLCANO_SYSTEM_NAMESPACE", "volcano-system"))

    bootstrap = REPO_ROOT / "scripts" / "volcano" / "bootstrap-kind.sh"
    _run(["bash", str(bootstrap)], env=env)

    _run(["kubectl", "config", "use-context", f"kind-{cluster_name}"], env=env)

    workload_namespace = env.get("VOLCANO_NAMESPACE") or "soma-agent-hub"
    _ensure_namespace(workload_namespace, env)

    _apply_queue_manifests(env)
    _wait_for_queue_ready("interactive", env)

    return {
        "namespace": workload_namespace,
        "cluster_name": cluster_name,
    }
