"""Shim to expose the repository-wide ``common`` package for the constitution service.

Tests prepend the service directory onto ``sys.path`` which hides the repository
root.  This module adds the root ``common`` directory to ``sys.path`` and merges
the namespace so that ``import common`` works inside the service.
"""

import pathlib
import pkgutil
import sys

from services.common.config.base_settings import resolve_env

repo_root = pathlib.Path(__file__).resolve().parents[2]
repo_common = repo_root / "common"
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(repo_common))
    __path__ = pkgutil.extend_path(__path__, __name__)
