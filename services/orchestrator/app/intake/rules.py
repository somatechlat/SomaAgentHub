"""Dependency and validation rules for intake modules."""

from __future__ import annotations

from typing import Dict, List


def resolve_missing_dependencies(module_id: str, answered_modules: List[str], dependency_map: Dict[str, List[str]]) -> List[str]:
    """Return dependencies that still need to be addressed for a module."""

    missing: List[str] = []
    for dependency in dependency_map.get(module_id, []):
        if dependency not in answered_modules:
            missing.append(dependency)
    return missing


def validate_dependency_closure(selected_modules: List[str], dependency_map: Dict[str, List[str]]) -> List[str]:
    """Ensure all required dependencies are present when users select modules manually."""

    violations: List[str] = []
    for module_id in selected_modules:
        missing = [dep for dep in dependency_map.get(module_id, []) if dep not in selected_modules]
        if missing:
            violations.append(f"Module '{module_id}' missing dependencies: {', '.join(missing)}")
    return violations
