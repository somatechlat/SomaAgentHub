from pathlib import Path

from app.static_templates.engine import (
build_default_tokens,
render_template_set,
TEMPLATE_ROOT,
)
from services.common.config.base_settings import resolve_env


def test_template_root_exists():
assert TEMPLATE_ROOT.exists()


def test_render_fastapi_tmp(tmp_path: Path):
tokens = build_default_tokens(
app_name="demo-app", image="demo/app:latest", service_port=8081
)
result = render_template_set("fastapi", tmp_path, tokens, zip_output=False)
main_py = result.output_dir / "app" / "main.py"
assert main_py.exists()
content = main_py.read_text(encoding="utf-8")
assert "demo-app" in content


def test_render_helm_values(tmp_path: Path):
tokens = build_default_tokens(
app_name="demo-app", image="demo/app", service_port=8081, namespace="ns1"
)
result = render_template_set(
"helm/generated-app", tmp_path, tokens, zip_output=False
)
values = result.output_dir / "values.yaml"
assert values.exists()
text = values.read_text(encoding="utf-8")
assert "ns1" in text and "demo/app" in text and "8081" in text
