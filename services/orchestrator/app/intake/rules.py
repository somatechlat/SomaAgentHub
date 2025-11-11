"""Dependency and validation rules for intake modules."""

from __future__ import annotations
from services.common.config.base_settings import resolve_env


def resolve_missing_dependencies(
    module_id: str, answered_modules: list[str], dependency_map: dict[str, list[str]]
) -> list[str]:
    """Return dependencies that still need to be addressed for a module."""

    missing: list[str] = []
    for dependency in dependency_map.get(module_id, []):
        if dependency not in answered_modules:
            missing.append(dependency)
    return missing


def validate_dependency_closure(
    selected_modules: list[str], dependency_map: dict[str, list[str]]
) -> list[str]:
    """Ensure all required dependencies are present when users select modules manually."""

    violations: list[str] = []
    for module_id in selected_modules:
        missing = [
            dep
            for dep in dependency_map.get(module_id, [])
            if dep not in selected_modules
        ]
        if missing:
            violations.append(
                f"Module '{module_id}' missing dependencies: {', '.join(missing)}"
            )
    return violations
