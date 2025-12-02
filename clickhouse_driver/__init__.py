"""Real ClickHouse driver package.

This module requires the real clickhouse_driver package to be installed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

try:
    import clickhouse_driver
    except ImportError:
    raise ImportError(
        "Real clickhouse_driver package required. Install with: pip install clickhouse-driver"
    )

# Export all real driver functionality
    __all__ = getattr(clickhouse_driver, "__all__", [name for name in dir(clickhouse_driver) if not name.startswith("__")])

# Mirror the real driver's public surface
    for name in __all__:
    globals()[name] = getattr(clickhouse_driver, name)