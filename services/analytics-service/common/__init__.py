
Tests prepend the ``services/analytics-service`` directory to ``sys.path`` and
then import ``common.config``.  Because the real ``common`` package lives at the
repository root (``../common``), Python cannot find it when only the service
extends its ``__path__`` to include the repository‑level ``common`` directory.
"""

import pathlib
import pkgutil
import sys
from services.common.config.base_settings import resolve_env

# Resolve the repository root (two levels up from this file: analytics-service -> services -> repo)
repo_root = pathlib.Path(__file__).resolve().parents[2]
repo_common = repo_root / "common"

# Ensure the repository ``common`` directory is on ``sys.path`` so the
# original package can be discovered.
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(repo_common))

    __path__ = pkgutil.extend_path(__path__, __name__)
