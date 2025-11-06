"""Identity service package.

This module ensures that the repository root is added to ``sys.path`` before
importing the central ``services._path_setup`` shim.  This is necessary when
tests change the current working directory to the service folder, which would
otherwise prevent the top‑level ``services`` package from being found.
"""

import pathlib
import sys

# The repository root is four levels up from this file (service/app/__init__.py).
_repo_root = pathlib.Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
	sys.path.insert(0, str(_repo_root))

import services._path_setup  # noqa: F401