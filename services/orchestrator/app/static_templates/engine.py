"""Static template rendering engine.

Copies version-controlled template sets from ``services/static-templates`` into a
workspace output directory, performing token substitution on text files.

Design goals:
    - Deterministic (no random artefacts); safe to run multiple times.
    - Narrow responsibility: copy + substitute + package (zip optional).
    - Side-effect free outside the provided output base directory.

    Tokens use ``{{TOKEN_NAME}}`` syntax. All tokens must be supplied; missing
    tokens raise ``ValueError`` to avoid silent bad renders.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

RE_TOKEN = re.compile(r"{{([A-Z0-9_]+)}}")

TEMPLATE_ROOT = Path(__file__).resolve().parents[3] / "static-templates"


@dataclass(slots=True)
class RenderResult:
    output_dir: Path
    zipped_path: Path | None
    tokens: dict[str, str]
    files_rendered: int


TEXT_EXTENSIONS: set[str] = {
    ".py",
    ".txt",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".jsx",
    ".js",
    ".html",
    ".sh",
    "Dockerfile",
}


def _iter_files(base: Path) -> Iterable[Path]:
    for p in base.rglob("*"):
        if p.is_file():
            yield p


def _is_text_file(path: Path) -> bool:
    """Heuristic by extension only (templates are controlled)"""
    return path.suffix in TEXT_EXTENSIONS or any(str(path).endswith(ext) for ext in TEXT_EXTENSIONS if ext)


def validate_tokens(content: str, provided: Mapping[str, str], *, file_path: Path) -> None:
    missing: set[str] = set()
    for match in RE_TOKEN.finditer(content):
        token = match.group(1)
        if token not in provided:
            missing.add(token)
    if missing:
        raise ValueError(f"Missing token(s) {sorted(missing)} in file {file_path}")


def substitute_tokens(content: str, provided: Mapping[str, str]) -> str:
    def _repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return provided.get(key, match.group(0))

    return RE_TOKEN.sub(_repl, content)


def render_template_set(
    template_set: str,
    destination_root: Path,
    tokens: Mapping[str, str],
    zip_output: bool = True,
    overwrite: bool = True,
) -> RenderResult:
    """Render a template set into ``destination_root / template_set``.

    Args:
        template_set: Name of top‑level template directory (e.g. ``fastapi``).
        destination_root: Base directory where artefacts are written.
        tokens: Mapping of ``TOKEN`` → value (must cover all occurrences).
        zip_output: Whether to zip the rendered tree (returns path).
        overwrite: If ``False`` and the directory exists, raises ``FileExistsError``.
    """

    source_dir = TEMPLATE_ROOT / template_set
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Template set '{template_set}' not found under {TEMPLATE_ROOT}")

    output_dir = destination_root / template_set
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Output directory {output_dir} already exists and overwrite=False")
        shutil.rmtree(output_dir)
    shutil.copytree(source_dir, output_dir)

    files_rendered = 0
    for file_path in _iter_files(output_dir):
        if not _is_text_file(file_path):
            continue
        raw = file_path.read_text(encoding="utf-8")
        validate_tokens(raw, tokens, file_path=file_path)
        rendered = substitute_tokens(raw, tokens)
        if rendered != raw:
            file_path.write_text(rendered, encoding="utf-8")
        # Rename files / directories if their names contain tokens
        if "{{" in file_path.name:
            new_name = substitute_tokens(file_path.name, tokens)
            file_path.rename(file_path.with_name(new_name))
            files_rendered += 1

    zipped_path: Path | None = None
    if zip_output:
        zipped_path = destination_root / f"{template_set}.zip"
        if zipped_path.exists():
            zipped_path.unlink()
        with zipfile.ZipFile(zipped_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in _iter_files(output_dir):
                arcname = file_path.relative_to(destination_root)
                zf.write(file_path, arcname)

    return RenderResult(
        output_dir=output_dir,
        zipped_path=zipped_path,
        tokens=dict(tokens),
        files_rendered=files_rendered,
    )


def build_default_tokens(
    app_name: str,
    image: str,
    service_port: int = 8000,
    frontend_port: int = 5173,
    namespace: str = "default",
    ingress_host: str | None = None,
    brand_color: str = "#3366ff",
    otel_exporter_endpoint: str = "http://otel-collector:4318",
) -> dict[str, str]:
    return {
        "APP_NAME": app_name,
        "IMAGE": image,
        "SERVICE_PORT": str(service_port),
        "FRONTEND_PORT": str(frontend_port),
        "NAMESPACE": namespace,
        "INGRESS_HOST": ingress_host or f"{app_name}.local",
        "BRAND_COLOR": brand_color,
        "OTEL_EXPORTER_ENDPOINT": otel_exporter_endpoint,
    }


__all__ = [
    "render_template_set",
    "build_default_tokens",
    "RenderResult",
]
