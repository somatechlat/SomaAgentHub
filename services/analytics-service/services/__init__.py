"""Namespace package for ``analytics-service``.

Tests prepend the ``services/analytics-service`` directory to ``sys.path`` and
then import ``services.analytics_service`` (or ``services.analytics_service.app``).
This file makes ``services`` a *namespace* package that merges with the root
``services`` package defined at the repository top level, allowing the import
to resolve to the actual service implementation located in the repository root.
"""

import pkgutil
from services.common.config.base_settings import resolve_env

__path__ = pkgutil.extend_path(__path__, __name__)
