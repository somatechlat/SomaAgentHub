import importlib.util
import pathlib
import types
import pytest


def _load_registry_module() -> types.ModuleType:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    mod_path = repo_root / "services" / "tool-service" / "tool_registry.py"
    spec = importlib.util.spec_from_file_location("tool_service_registry", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.mark.parametrize("tool_name", ["terraform", "playwright", "github"])
def test_adapter_protocol_health(tool_name: str):
    module = _load_registry_module()
    registry = module.tool_registry
    credentials = {"access_token": "dummy"} if tool_name == "github" else None
    adapter = registry.get_adapter(tool_name, credentials)
    assert hasattr(adapter, "health_check"), "Adapter must implement health_check()"
    try:
        health = adapter.health_check()
    except Exception as exc:  # pragma: no cover - adapter anomaly
        pytest.fail(f"health_check raised: {exc}")
    assert isinstance(health, dict)
