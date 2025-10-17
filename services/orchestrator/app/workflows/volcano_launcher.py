"""Utilities to submit ad-hoc jobs to Volcano queues.

The launcher uses the local kubectl binary to keep the spike dependency-free.
It renders PodGroup and Job manifests via PyYAML and streams them to kubectl.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import yaml

from ..core.config import settings


class VolcanoLauncherError(RuntimeError):
    """Raised when job submission or monitoring fails."""


@dataclass(slots=True)
class VolcanoJobSpec:
    """Minimal description of a Volcano-managed batch job."""

    job_name: str
    queue: str
    image: str
    command: Sequence[str]
    env: Mapping[str, str] = field(default_factory=dict)
    min_member: int = 1
    cpu: str = "500m"
    memory: str = "512Mi"


class VolcanoJobLauncher:
    """Submit and monitor Volcano jobs via kubectl."""

    def __init__(self, namespace: str | None = None, kubectl_binary: str | None = None) -> None:
        self.namespace = namespace or settings.volcano_namespace
        self.kubectl = kubectl_binary or settings.kubectl_binary
        if shutil.which(self.kubectl) is None:
            raise VolcanoLauncherError(
                f"kubectl binary '{self.kubectl}' not found in PATH; cannot launch Volcano jobs"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def submit(self, spec: VolcanoJobSpec) -> str:
        """Submit the PodGroup/Job manifest."""

        manifest = self._render_manifest(spec)
        self._kubectl(["apply", "-f", "-"], input_data=manifest)
        return spec.job_name

    def wait_for_completion(self, job_name: str, timeout_seconds: int) -> None:
        """Block until the job completes or timeout expires."""

        self._kubectl(
            [
                "wait",
                f"job/{job_name}",
                "--for=condition=complete",
                f"--timeout={timeout_seconds}s",
                "-n",
                self.namespace,
            ]
        )

    def fetch_logs(self, job_name: str) -> str:
        """Return aggregated job logs."""

        result = self._kubectl(
            ["logs", f"job/{job_name}", "-n", self.namespace],
            capture_output=True,
        )
        return result.decode("utf-8") if isinstance(result, bytes) else result

    def delete(self, job_name: str, queue_name: str | None = None) -> None:
        """Best-effort cleanup for job + PodGroup (and optional queue)."""

        self._kubectl(
            ["delete", f"job/{job_name}", "-n", self.namespace, "--ignore-not-found"],
            check=False,
        )
        self._kubectl(
            ["delete", f"podgroup/{job_name}", "-n", self.namespace, "--ignore-not-found"],
            check=False,
        )
        if queue_name:
            self._kubectl(["delete", f"queue/{queue_name}", "--ignore-not-found"], check=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_manifest(self, spec: VolcanoJobSpec) -> str:
        """Return PodGroup + Job manifest as YAML string."""

        task_spec_json = json.dumps({
            "minMember": spec.min_member,
            "minResources": {"cpu": spec.cpu, "memory": spec.memory},
        })

        podgroup = {
            "apiVersion": "scheduling.volcano.sh/v1beta1",
            "kind": "PodGroup",
            "metadata": {
                "name": spec.job_name,
                "namespace": self.namespace,
                "labels": {
                    "app.kubernetes.io/managed-by": "somaagenthub",
                    "volcano.sh/queue-name": spec.queue,
                },
            },
            "spec": {
                "minMember": spec.min_member,
                "minResources": {"cpu": spec.cpu, "memory": spec.memory},
            },
        }

        job = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": spec.job_name,
                "namespace": self.namespace,
                "labels": {"app.kubernetes.io/managed-by": "somaagenthub"},
                "annotations": {
                    "scheduling.k8s.io/group-name": spec.job_name,
                    "volcano.sh/queue-name": spec.queue,
                    "volcano.sh/task-spec": task_spec_json,
                },
            },
            "spec": {
                "template": {
                    "metadata": {"labels": {"app": spec.job_name}},
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [
                            {
                                "name": "worker",
                                "image": spec.image,
                                "command": list(spec.command),
                                "env": [
                                    {"name": key, "value": value}
                                    for key, value in spec.env.items()
                                ],
                                "resources": {
                                    "requests": {"cpu": spec.cpu, "memory": spec.memory},
                                    "limits": {"cpu": spec.cpu, "memory": spec.memory},
                                },
                            }
                        ],
                    },
                },
            },
        }

        manifest_parts = [
            yaml.safe_dump(podgroup, sort_keys=False),
            yaml.safe_dump(job, sort_keys=False),
        ]
        return "---\n".join(part.strip() for part in manifest_parts if part)

    def _kubectl(
        self,
        args: Sequence[str],
        *,
        input_data: str | None = None,
        capture_output: bool = False,
        check: bool = True,
    ) -> bytes | str | None:
        """Invoke kubectl with common defaults."""

        cmd = [self.kubectl, *args]
        # `-f -` requires namespace to be present in the manifest, so we do not append `-n` here.
        if input_data is not None:
            result = subprocess.run(
                cmd,
                input=input_data.encode("utf-8"),
                capture_output=True,
                check=check,
            )
            if result.returncode != 0 and check:
                raise VolcanoLauncherError(result.stderr.decode("utf-8"))
            return result.stdout

        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            check=check,
        )
        if result.returncode != 0 and check:
            raise VolcanoLauncherError(result.stderr.decode("utf-8"))
        if capture_output:
            return result.stdout
        return None


def default_session_spec(session_id: str) -> VolcanoJobSpec:
    """Convenience factory used by session workflows."""

    job_name = _slugify(f"session-{session_id}")
    session_literal = json.dumps(session_id)
    default_command = [
        "python",
        "-c",
        textwrap.dedent(
            """
            import json, time
            payload = {"session_id": %(session_literal)s}
            print("[volcano] executing session payload", json.dumps(payload))
            time.sleep(2)
            print("[volcano] done")
            """
        ).strip()
        % {"session_literal": session_literal},
    ]
    return VolcanoJobSpec(
        job_name=job_name,
        queue=settings.volcano_default_queue,
        image=settings.volcano_session_image,
        command=default_command,
        cpu=settings.volcano_session_cpu,
        memory=settings.volcano_session_memory,
    )


def _slugify(value: str) -> str:
    """Return DNS-compatible job names."""

    sanitized = value.lower()
    allowed = [ch if ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch == "-" else "-" for ch in sanitized]
    slug = "".join(allowed).strip("-")
    return slug or "session-job"
