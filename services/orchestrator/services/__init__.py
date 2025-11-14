"""Namespace package for ``orchestrator`` service.

Enables imports like ``services.orchestrator.app.main`` when the test adds
the ``services/orchestrator`` directory to ``sys.path``.
"""

import pkgutil
from services.common.config.base_settings import resolve_env

__path__ = pkgutil.extend_path(__path__, __name__)
