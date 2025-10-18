import importlib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

volcano_module = importlib.import_module(
    "services.orchestrator.app.workflows.volcano_launcher"
)
VolcanoJobLauncher = volcano_module.VolcanoJobLauncher
VolcanoJobSpec = volcano_module.VolcanoJobSpec

_activities_path = ROOT / "services" / "orchestrator" / "workflows" / "activities.py"
_spec = importlib.util.spec_from_file_location(
    "services.orchestrator.workflows.activities", _activities_path
)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise RuntimeError("Unable to load activities module for testing")
activities = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = activities
_spec.loader.exec_module(activities)


def test_render_manifest_honors_parallelism_and_ttl(monkeypatch):
    launcher = VolcanoJobLauncher(namespace="test-ns", kubectl_binary="true")
    spec = VolcanoJobSpec(
        job_name="demo-job",
        queue="interactive",
        image="python:3.11-slim",
        command=["python", "-m", "demo"],
        env={"FOO": "bar"},
        min_member=3,
        cpu="2",
        memory="1Gi",
        parallelism=3,
        completions=5,
        ttl_seconds_after_finished=120,
    )

    manifest = launcher._render_manifest(spec)
    podgroup, job = list(yaml.safe_load_all(manifest))

    assert podgroup["spec"]["minMember"] == 3
    assert podgroup["metadata"]["namespace"] == "test-ns"

    job_spec = job["spec"]
    assert job_spec["parallelism"] == 3
    assert job_spec["completions"] == 5
    assert job_spec["ttlSecondsAfterFinished"] == 120
    container = job_spec["template"]["spec"]["containers"][0]
    assert container["env"] == [{"name": "FOO", "value": "bar"}]
    assert container["resources"]["requests"] == {"cpu": "2", "memory": "1Gi"}


@pytest.mark.asyncio
async def test_launch_volcano_session_job_overrides_gang_fields(monkeypatch):
    monkeypatch.setattr(activities.settings, "enable_volcano_scheduler", True)
    monkeypatch.setattr(activities.settings, "volcano_job_timeout_seconds", 45)

    captured = {}

    class DummyLauncher:
        def submit(self, spec):
            captured["spec"] = spec
            return spec.job_name

        def wait_for_completion(self, job_name, timeout):
            captured["wait_args"] = (job_name, timeout)

        def fetch_logs(self, job_name):
            captured["fetched_logs_for"] = job_name
            return "LOGS"

    async def immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(activities, "VolcanoJobLauncher", lambda: DummyLauncher())
    monkeypatch.setattr(activities.asyncio, "to_thread", immediate_to_thread)

    payload = {
        "session_id": "abc123",
        "wait": True,
        "queue": "critical",
        "command": ["python", "worker.py"],
        "env": {"FOO": "bar"},
        "cpu": "2",
        "memory": "4Gi",
        "min_member": 4,
        "parallelism": 5,
        "completions": 6,
        "ttl_seconds_after_finished": 90,
    }

    result = await activities.launch_volcano_session_job(payload)

    spec = captured["spec"]
    assert spec.queue == "critical"
    assert spec.cpu == "2"
    assert spec.memory == "4Gi"
    assert spec.command == ["python", "worker.py"]
    assert spec.env["FOO"] == "bar"
    assert spec.min_member == 5  # normalized to match parallelism
    assert spec.parallelism == 5
    assert spec.completions == 6
    assert spec.ttl_seconds_after_finished == 90

    assert captured["wait_args"] == (spec.job_name, 45)
    assert captured["fetched_logs_for"] == spec.job_name

    assert result == {
        "status": "submitted",
        "job_name": spec.job_name,
        "waited": True,
        "logs": "LOGS",
    }
