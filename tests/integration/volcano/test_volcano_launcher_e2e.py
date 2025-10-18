from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.orchestrator.app.workflows.volcano_launcher import (  # noqa: E402
    VolcanoJobLauncher,
    VolcanoJobSpec,
)


def test_volcano_launcher_executes_job_end_to_end(volcano_sandbox: dict[str, str]) -> None:
    namespace = volcano_sandbox["namespace"]

    job_name = f"volcano-int-{uuid4().hex[:10]}"
    spec = VolcanoJobSpec(
        job_name=job_name,
        queue="interactive",
        image="python:3.11-slim",
        command=[
            "python",
            "-c",
            "import time; print('volcano integration job start'); "
            "time.sleep(1); print('volcano integration job done')",
        ],
        env={"VOLCANO_TEST": "true"},
        min_member=1,
        cpu="250m",
        memory="256Mi",
        parallelism=1,
        completions=1,
        ttl_seconds_after_finished=60,
    )

    launcher = VolcanoJobLauncher(namespace=namespace)

    try:
        submitted_name = launcher.submit(spec)
        assert submitted_name == job_name

        launcher.wait_for_completion(job_name, timeout_seconds=180)
        logs = launcher.fetch_logs(job_name)
    finally:
        launcher.delete(job_name)

    if isinstance(logs, bytes):
        logs = logs.decode("utf-8")

    assert "volcano integration job start" in logs
    assert "volcano integration job done" in logs
