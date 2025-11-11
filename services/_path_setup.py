"""Centralized import‑path shim for the repository.

The test harness prepends the individual service directory (e.g. ``services/analytics-service``)
to ``sys.path`` before importing ``app`` modules.  Many services also import top‑level
packages such as ``common`` or ``services`` itself.  To make those imports work
reliably we need the repository root on ``sys.path`` **after** the service
directory.  Previously each service's ``app/__init__.py`` performed this logic
independently, which led to duplication and inconsistencies.

This module performs the path manipulation once.  Importing it (e.g.
``import services._path_setup``) ensures the repository root is appended to
``sys.path`` if it is not already present.
"""

from __future__ import annotations

import pathlib
import sys
from services.common.config.base_settings import resolve_env

# The repository root is the parent of the ``services`` package directory.
_repo_root = pathlib.Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    # Append rather than prepend so the service‑specific directory (added by
    # the test harness at index 0) remains the first entry, preserving the
    # expected import order for service‑local modules.
    sys.path.append(str(_repo_root))


# Export a no‑op name for ``from services._path_setup import *`` compatibility.
def ensure_repo_root() -> None:  # pragma: no cover
    """Explicitly ensure the repository root is on ``sys.path``.

    The function is kept for backward compatibility; importing the module is
    sufficient because the side‑effect runs at import time.
    """
    return None
