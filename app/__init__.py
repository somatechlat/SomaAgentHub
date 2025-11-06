"""Top‑level ``app`` namespace package.

Each service (e.g. ``analytics-service``, ``constitution-service``) contains
its own ``app`` subpackage with FastAPI entrypoints.  The test harness prepends
the individual service directory to ``sys.path`` and then imports modules such
as ``app.main`` or ``app.core.constitution``.  Without a package named ``app``
at the repository root those imports fail because Python looks for a top‑level
``app`` package on ``sys.path`` and finds none.

By providing a *namespace* package here we allow the ``app`` directories from
different services to be merged.  The ``pkgutil.extend_path`` call combines the
``app`` packages found under each service with this top‑level package.  We also
ensure the repository root is on ``sys.path`` (the ``sitecustomize`` shim
already appends it, but we add a defensive check).
"""

import pkgutil
import pathlib
import sys

# Make ``app`` a namespace package that can span multiple service directories.
__path__ = pkgutil.extend_path(__path__, __name__)

# Ensure the repository root is present on ``sys.path`` so that the top‑level
# ``app`` package can be discovered when services are imported.
repo_root = pathlib.Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))
