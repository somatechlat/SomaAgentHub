"""Namespace package to allow tests that prepend 'services/jobs' to sys.path to import the top-level 'services' package.

This file uses pkgutil.extend_path so that the 'services' package can be split across
multiple locations (the repository root and the test's added path).
"""

import pkgutil
from services.common.config.base_settings import resolve_env

__path__ = pkgutil.extend_path(__path__, __name__)
