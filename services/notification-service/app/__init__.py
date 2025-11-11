"""Notification orchestrator service package.

Import the central path‑setup shim so that the repository root is added to
``sys.path`` for imports such as ``common``.
"""

import services._path_setup  # noqa: F401
from services.common.config.base_settings import resolve_env
