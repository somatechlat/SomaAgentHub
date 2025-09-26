"""Static adapter registry used by the tool service."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict

from .config import Settings, get_settings
from .security import compute_manifest_digest, compute_release_signature


def _build_registry(settings: Settings) -> Dict[str, dict]:
    adapters = {
        "plane": {
            "id": "plane",
            "name": "Plane.so",
            "status": "available",
            "version": "1.0.0",
            "rate_limit_per_minute": 20,
            "billing": {
                "service": "tool-plane",
                "cost_per_call": 0.002,
                "currency": settings.billing_default_currency,
            },
            "manifest": {
                "actions": [
                    {
                        "name": "create_project",
                        "params": ["name", "workspace_id"],
                    },
                    {
                        "name": "add_member",
                        "params": ["project_id", "user"],
                    },
                ],
                "permissions": ["projects:write", "memberships:write"],
            },
            "source": "manual",
            "signed_at": "2024-05-01T00:00:00Z",
        },
        "github": {
            "id": "github",
            "name": "GitHub",
            "status": "available",
            "version": "2.3.1",
            "rate_limit_per_minute": 15,
            "billing": {
                "service": "tool-github",
                "cost_per_call": 0.001,
                "currency": settings.billing_default_currency,
            },
            "manifest": {
                "actions": [
                    {
                        "name": "create_issue",
                        "params": ["repository", "title", "body"],
                    },
                    {
                        "name": "merge_pull_request",
                        "params": ["repository", "number"],
                    },
                ],
                "permissions": ["issues:write", "pulls:write"],
            },
            "source": "auto",
            "signed_at": "2024-05-01T00:00:00Z",
        },
    }
    for adapter in adapters.values():
        manifest = adapter.get("manifest")
        manifest_digest = compute_manifest_digest(manifest) if manifest else None
        if manifest_digest:
            adapter["manifest_digest"] = manifest_digest
        adapter["signature"] = compute_release_signature(
            adapter["id"],
            adapter["version"],
            settings.release_signing_secret,
            manifest_digest=manifest_digest,
        )
    return adapters


_REGISTRY: Dict[str, dict] | None = None


def get_registry(settings: Settings | None = None) -> Dict[str, dict]:
    global _REGISTRY
    if _REGISTRY is None:
        cfg = settings or get_settings()
        _REGISTRY = _build_registry(cfg)
    return _REGISTRY


def list_adapters(settings: Settings | None = None) -> list[dict]:
    registry = get_registry(settings)
    return [deepcopy(adapter) for adapter in registry.values()]


def get_adapter(adapter_id: str, settings: Settings | None = None) -> dict | None:
    registry = get_registry(settings)
    adapter = registry.get(adapter_id)
    return deepcopy(adapter) if adapter else None
