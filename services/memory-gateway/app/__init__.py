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

import pkgutil
import pathlib
import sys

# Extend the ``app`` namespace to include subpackages from other services.
__path__ = pkgutil.extend_path(__path__, __name__)

# Make sure the repository root is present on ``sys.path``.
repo_root = pathlib.Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
	sys.path.append(str(repo_root))
