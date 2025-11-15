"""Analytics service package.

This package ensures that the repository root is placed at the front of
``sys.path`` so that the top‑level ``services`` namespace package (which
available for all subsequent imports.
"""

import pathlib
import sys

# Determine the repository root (four levels up from this file) and prepend it
# to ``sys.path`` if it is not already present.
_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import services._path_setup  # noqa: F401,E402
from services.common.config.base_settings import resolve_env

# Analytics service ``app`` package – kept minimal to allow the top‑level
# ``app`` namespace package (defined at the repository root) to merge this
# directory with other services' ``app`` packages via ``pkgutil.extend_path``.
