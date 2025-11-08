"""Local ``common`` package shim for the analytics service.

Tests prepend the ``services/analytics-service`` directory to ``sys.path`` and
then import ``common.config``.  Because the real ``common`` package lives at the
repository root (``../common``), Python cannot find it when only the service
directory is on ``sys.path``.  This shim creates a *namespace* package that
extends its ``__path__`` to include the repository‑level ``common`` directory.
"""

import pathlib
import pkgutil
import sys

# Resolve the repository root (two levels up from this file: analytics-service -> services -> repo)
repo_root = pathlib.Path(__file__).resolve().parents[2]
repo_common = repo_root / "common"

# Ensure the repository ``common`` directory is on ``sys.path`` so the
# original package can be discovered.
if str(repo_common) not in sys.path:
    sys.path.insert(0, str(repo_common))

# Merge this shim with the real ``common`` package.
__path__ = pkgutil.extend_path(__path__, __name__)
