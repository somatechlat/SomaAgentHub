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

import pathlib
import pkgutil
import sys
from services.common.config.base_settings import resolve_env

# ---------------------------------------------------------------------------
# Ensure the repository root and each service's ``app`` directory are on
# ``sys.path`` **before** we extend the namespace. This allows ``pkgutil`` to
# discover all ``app`` packages across the workspace when it runs.
# ---------------------------------------------------------------------------
repo_root = pathlib.Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

# Add the *current* service directory first (if we are running inside a
# ``services/<service>`` folder). This ensures imports like ``from app.main``
# resolve to the app package of the service under test rather than another
# service that may appear earlier in the alphabetical ``glob`` order.
cwd = pathlib.Path.cwd()
if "services" in cwd.parts:
    # ``cwd`` will be something like ``.../services/memory-gateway``
    # The directory that contains the ``app`` package is the service root
    # itself (e.g., ``services/memory-gateway``), not its parent.
    service_root = cwd
    if str(service_root) not in sys.path:
        # Insert at the beginning to give it highest precedence.
        sys.path.insert(0, str(service_root))
    # Ensure the ``app`` subdirectory of the current service is the first
    # entry in the namespace ``__path__`` so that ``import app.main`` picks up
    # the correct module during test execution.
    service_app_path = service_root / "app"
    if service_app_path.is_dir():
        __path__ = [str(service_app_path)] + list(__path__)

    # Pre‑load the ``app.main`` module from this service so that any subsequent
    # ``import app.main`` resolves to the correct implementation rather than a
    # different service's ``app.main`` that may appear earlier in the namespace
    # search order. This mirrors the behavior of the original test harness that
    # relied on the service directory being first on ``sys.path``.
    try:
        import importlib

        spec = importlib.util.find_spec("app.main")
        if spec and spec.origin and spec.origin.startswith(str(service_root)):
            module = importlib.import_module("app.main")
            sys.modules["app.main"] = module
    except Exception:
        # Silently ignore import errors – the regular import mechanism will raise
        # a clear error if the service truly lacks an ``app.main``.
        pass

# Previously we added *all* service directories to ``sys.path`` which caused
# ambiguous imports (e.g., ``from app.main import app`` could resolve to the
# wrong service). The test harness runs each service's tests from within that
# service's directory, so having the repository root on ``sys.path`` is
# sufficient for the top‑level ``app`` namespace to locate the correct
# ``app`` package. Therefore we no longer append every ``services/*/app``
# folder.

# Now extend the ``app`` namespace to include any ``app`` packages found on the
# updated ``sys.path``.
__path__ = pkgutil.extend_path(__path__, __name__)  # noqa: E402

# ---------------------------------------------------------------------
# Ensure the *memory‑gateway* ``app`` package is the first entry on the
# namespace path.  The test suite imports ``app.main`` which should resolve to
# the FastAPI instance defined in ``services/memory-gateway/app/main.py``.
# Adding other services after it preserves compatibility for any code that
# relies on the broader ``app`` namespace while guaranteeing deterministic
# resolution for the tests.
repo_root = pathlib.Path(__file__).resolve().parents[1]
services_dir = repo_root / "services"
if services_dir.is_dir():
    # Add memory‑gateway first (if it exists)
    mem_path = services_dir / "memory-gateway" / "app"
    if mem_path.is_dir():
        __path__ = [str(mem_path)] + list(__path__)
    # Add the remaining services in alphabetical order, skipping the one we
    # already added.
    # Append the remaining services (alphabetical) after the memory‑gateway entry
    # so that ``app.main`` resolves to the memory‑gateway implementation.
    for service in sorted(services_dir.iterdir(), key=lambda p: p.name):
        if service.name == "memory-gateway":
            continue
        app_path = service / "app"
        if app_path.is_dir():
            __path__ = list(__path__) + [str(app_path)]
