"""Jobs service package.

Ensure the repository root is at the front of ``sys.path`` and reorder
the top-level ``app`` namespace to prioritize this service's app directory.
"""

import pathlib
import sys
import importlib

_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    # Insert at the beginning to give priority over the service‑specific path.
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
    print('DEBUG: failed to reorder app.__path__ in jobs:', e)