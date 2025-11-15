"""Top‑level ``app`` namespace package for the Memory‑Gateway service.

Each service (e.g. ``memory-gateway``, ``policy-engine``) provides its own
``app`` subpackage containing FastAPI entrypoints.  The test harness adds the
service directory to ``sys.path`` and then imports ``app.main``.  Without a
package named ``app`` at the repository root those imports would fail because
Python looks for a top‑level ``app`` package on ``sys.path`` and finds none.

This file makes ``app`` a *namespace* package that can span multiple service
directories, mirroring the implementation in the repository root ``app``
package.  It also ensures the repository root is on ``sys.path`` so imports
resolve correctly during testing and when the service runs in isolation.
"""

import pathlib
import pkgutil
import sys
from services.common.config.base_settings import resolve_env

# Extend the ``app`` namespace to include subpackages from other services.
__path__ = pkgutil.extend_path(__path__, __name__)

# Make sure the repository root is present on ``sys.path``.
# The ``app`` package lives inside ``services/memory-gateway/app``. When the
# test suite runs from the repository root, that directory is not automatically
# on ``sys.path``. Adding the service root (two levels up from this file) ensures
# that ``import app.main`` resolves to the FastAPI application defined for the
# memory‑gateway service.
service_root = pathlib.Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
# Insert at the front so it takes precedence over any other ``app``
# packages that might appear earlier on ``sys.path``.
    sys.path.insert(0, str(service_root))
