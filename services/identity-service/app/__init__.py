"""Identity service package.

This module ensures that the repository root is added to ``sys.path`` and
reorders the top-level ``app`` namespace to prioritize this service's app directory.
"""

import pathlib
import sys
import importlib

# The repository root is four levels up from this file (service/app/__init__.py).
_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import services._path_setup  # noqa: F401

# Reorder the top‑level ``app`` namespace to prioritize this service.
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
    print('DEBUG: failed to reorder app.__path__ in identity-service:', e)