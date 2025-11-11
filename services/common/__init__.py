"""Shim to expose the top‑level ``common`` package under the ``services``
namespace.

Tests sometimes import ``services.common`` (e.g. the OPA client test).  The
actual ``common`` package lives at the repository root.  By adding this shim
and extending the package path we make ``services.common`` resolve to the same
module hierarchy.
"""

import pathlib
import pkgutil
import sys
from services.common.config.base_settings import resolve_env

# Repository root (two levels up from this file: services/common -> services -> repo)
repo_root = pathlib.Path(__file__).resolve().parents[2]
repo_common = repo_root / "common"
if str(repo_common) not in sys.path:
    sys.path.insert(0, str(repo_common))

# Merge with any other ``services.common`` namespace packages.
__path__ = pkgutil.extend_path(__path__, __name__)
