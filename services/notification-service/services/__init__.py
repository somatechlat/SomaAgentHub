"""Namespace package for ``notification-service``.

Allows imports like ``services.notification_service`` when the test adds the
service directory to ``sys.path``.
"""

import pkgutil
from services.common.config.base_settings import resolve_env

__path__ = pkgutil.extend_path(__path__, __name__)
