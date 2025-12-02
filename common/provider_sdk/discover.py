iscovery skeleton for provider adapters.

re design:
    - Provide registry decorators to register adapters.
    - Walk entry points or modules to discover available providers.
    - Expose a `discover()` function returning adapter metadata.
    """

    from __future__ import annotations

    from typing import Any
    from services.common.config.base_settings import resolve_env


    def discover() -> list[dict[str, Any]]:
    """Return an empty provider list for now (skeleton)."""
    return []
