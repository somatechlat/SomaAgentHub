"""Compatibility shim exposing the historical `slm` package as `somallm_provider`.

The full package rename will happen progressively; downstream code should import
from `somallm_provider` going forward.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

# Modules we lazily proxy from the legacy `slm` package.
_LEGACY_MODULES = {
    "adapters": "slm.adapters",
    "data": "slm.data",
    "local_models": "slm.local_models",
    "metrics": "slm.metrics",
    "producer": "slm.producer",
    "worker": "slm.worker",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - module level delegation
    if name in _LEGACY_MODULES:
        module = import_module(_LEGACY_MODULES[name])
        globals()[name] = module
        return module
    raise AttributeError(f"module 'somallm_provider' has no attribute '{name}'")


def __dir__() -> list[str]:  # pragma: no cover - module metadata
    return sorted(list(_LEGACY_MODULES.keys()))
