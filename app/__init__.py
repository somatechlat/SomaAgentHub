"""Top‑level ``app`` namespace package.

Each service (e.g. ``analytics-service``, ``identity-service``) contains its
own ``app`` subpackage with FastAPI entrypoints.  The test harness prepends the
service directory to ``sys.path`` and then imports ``app.main`` or other
modules under ``app``.  Without a package named ``app`` at the repository root
those imports fail because Python searches for a top‑level ``app`` package on
``sys.path`` and finds none.

By providing a *namespace* package here we allow the ``app`` directories from
different services to be merged.  The ``pkgutil.extend_path`` call combines the
``app`` packages found under each service with this top‑level package.
"""

import importlib
import pathlib
import sys
import pkgutil

# Make ``app`` a namespace package that can span multiple service directories.
__path__ = pkgutil.extend_path(__path__, __name__)

def _detect_service_app_path() -> str | None:
    """Return the filesystem path of the ``app`` directory for the active
    service (the one that appears first on ``sys.path``).

    The test harness adds the service directory (e.g. ``.../services/identity-service``)
    as ``sys.path[0]`` before any imports.  If that entry points to a service
    folder we locate its ``app`` subdirectory.
    """
    print('>>> app/__init__ detect: sys.path[0]=', sys.path[0] if sys.path else None)
    if not sys.path:
        return None
    first = pathlib.Path(sys.path[0])
    if first.is_dir() and first.parent.name == "services":
        app_dir = first / "app"
        if app_dir.is_dir():
            print('>>> app/__init__ detect: found service app path', app_dir)
            return str(app_dir)
    print('>>> app/__init__ detect: no service app path detected')
    return None

svc_app_path = _detect_service_app_path()
if svc_app_path and svc_app_path not in __path__:
    __path__.insert(0, svc_app_path)

# Defensive: ensure the repository root is on ``sys.path`` (sitecustomize already
# does this, but we keep the check for completeness).
repo_root = pathlib.Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))
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

