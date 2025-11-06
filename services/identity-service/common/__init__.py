"""Shim to expose repository-wide ``common`` package for the identity service.

The test suite adds the service directory to ``sys.path`` which hides the
repository root.  This module ensures the ``common`` directory is reachable and
merged as a namespace package.
"""

import pkgutil
import pathlib
import sys

repo_root = pathlib.Path(__file__).resolve().parents[2]
repo_common = repo_root / "common"
if str(repo_common) not in sys.path:
    sys.path.insert(0, str(repo_common))
__path__ = pkgutil.extend_path(__path__, __name__)