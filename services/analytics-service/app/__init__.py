"""Analytics service package.

This package ensures that the repository root is placed at the front of
``sys.path`` so that the top‑level ``services`` namespace package (which
contains the central ``_path_setup`` shim) can be imported correctly.  After
adjusting ``sys.path`` we import the shim to guarantee the repository root is
available for all subsequent imports.
"""

import pathlib
import sys

# Determine the repository root (four levels up from this file) and prepend it
# to ``sys.path`` if it is not already present.
_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Import the central path‑setup shim to finalize the import‑path configuration.
import services._path_setup  # noqa: F401

# Ensure the top‑level ``app`` namespace resolves to this service first.
import importlib, pathlib
try:
    top_app = importlib.import_module('app')
    my_dir = str(pathlib.Path(__file__).parent)
    if hasattr(top_app, '__path__'):
        path_list = list(top_app.__path__)
        if my_dir in path_list:
            path_list.remove(my_dir)
        path_list.insert(0, my_dir)
        top_app.__path__ = path_list
except Exception as e:
    print('DEBUG: failed to reorder app.__path__ in analytics-service:', e)

# Analytics service ``app`` package – kept minimal to allow the top‑level
# ``app`` namespace package (defined at the repository root) to merge this
# directory with other services' ``app`` packages via ``pkgutil.extend_path``.
