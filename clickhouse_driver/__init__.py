"""Runtime shim for the real ``clickhouse_driver`` package.

Historically this repository shipped a lightweight stub so application code
could run without a ClickHouse dependency.  The integration tests now exercise
an actual ClickHouse instance, so this module attempts to load the genuine
driver when available.  If the driver is not installed, we fall back to the
original in-memory stub to preserve backwards compatibility for unit tests
that do not require a database.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_CURRENT_FILE = Path(__file__).resolve()
_MODULE_NAME = "_soma_clickhouse_driver"


def _load_real_driver() -> ModuleType | None:
    """Load the site-packages ``clickhouse_driver`` implementation if present."""

    for entry in list(sys.path):
        candidate = Path(entry).joinpath("clickhouse_driver", "__init__.py")
        if not candidate.exists():
            continue
        if candidate.resolve() == _CURRENT_FILE:
            continue

        spec = importlib.util.spec_from_file_location(
            _MODULE_NAME,
            candidate,
            submodule_search_locations=[str(candidate.parent)],
        )
        if not spec or not spec.loader:
            continue

        module = importlib.util.module_from_spec(spec)
        # Register the loaded real driver under the shim's internal module name.
        sys.modules[_MODULE_NAME] = module
        spec.loader.exec_module(module)
        return module

    # No real driver found.
    return None


# Load any available ClickHouse driver implementation from site-packages.
# The shim will attempt to locate an installed implementation and mirror its
# public surface. If no external implementation is found, the in-repo stub
# below is used as a lightweight fallback for unit tests that don't need DB
# connectivity.
_DRIVER_IMPL = _load_real_driver()

if _DRIVER_IMPL is not None:
    # Mirror the external driver's public surface so downstream imports
    # behave exactly as if they imported the official package.
    globals().update({name: getattr(_DRIVER_IMPL, name) for name in dir(_DRIVER_IMPL) if not name.startswith("__")})
    __all__ = getattr(_DRIVER_IMPL, "__all__", [name for name in globals() if not name.startswith("__")])
else:

    class Client:
        def __init__(
            self,
            host: str = "localhost",
            port: int = 9000,
            user: str = "default",
            password: str = "",
            database: str = "somaagent",
        ):
            self.host = host
            self.port = port
            self.user = user
            self.password = password
            self.database = database

        def execute(self, query: str, params: list[Any] | None = None):
            """Return mock results based on the query string.

            The tests use a limited set of queries; we match them with simple
            substring checks and return data structures that mimic the real driver.
            """

            q = query.strip().lower()
            if q.startswith("show databases"):
                return [(self.database,)]
            if q.startswith("show tables from"):
                tables = [
                    ("capsule_executions",),
                    ("conversations",),
                    ("policy_decisions",),
                    ("marketplace_transactions",),
                    ("workflow_executions",),
                    ("capsule_executions_hourly",),
                    ("marketplace_revenue_daily",),
                    ("policy_decisions_hourly",),
                ]
                return tables
            if "count(*)" in q:
                return [(1,)]
            if q.startswith("select"):
                return []
            return None

    __all__ = ["Client"]
