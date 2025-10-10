"""Discovery skeleton for provider adapters.

Future design:
- Provide registry decorators to register adapters.
- Walk entry points or modules to discover available providers.
- Expose a `discover()` function returning adapter metadata.
"""

from __future__ import annotations

from typing import Any


def discover() -> list[dict[str, Any]]:
    """Return an empty provider list for now (skeleton)."""
    return []
