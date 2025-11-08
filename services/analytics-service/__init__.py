"""Namespace package for the analytics service.

Provides ``services.analytics_service`` import path for tests that prepend the
service directory to ``sys.path``.  It merges with the top‑level ``services``
namespace package via ``pkgutil.extend_path``.
"""

import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)
