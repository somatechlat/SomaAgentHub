"""Site customization for test environment.

This module is automatically imported by Python when the ``site`` module is
initialised (i.e., when a ``sitecustomize.py`` file is found on ``sys.path``).
It performs two duties:

1. **Ensure the repository root is on ``sys.path``** – The test suite adds the
    individual service directories to the front of ``sys.path`` before importing
    modules.  Because those service directories do not contain the top‑level
    ``common`` or ``app`` packages, imports such as ``import common.config`` or
    ``import app.core`` would fail unless the repository root is already on the
    import search path.  By inserting the absolute path of the repository root at
    the start of ``sys.path`` we guarantee that all namespace packages defined
    at the repository level are discoverable regardless of the order in which
    test code manipulates ``sys.path``.

2. **Patch ``testcontainers``' ``RedisContainer``** – Some versions of the
    ``testcontainers`` library lack the ``get_connection_url`` method required by
    the identity‑service tests.  The original implementation of this shim
    remains unchanged; we only add the repository‑path logic before it.
"""

import importlib
import os
import sys
from pathlib import Path
import sys
# Debug: indicate that sitecustomize has been loaded (appears in pytest output)
print('>>> sitecustomize loaded')

# ---------------------------------------------------------------------------
# 1. Ensure the repository root is on ``sys.path``.
# ---------------------------------------------------------------------------
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    # Append the repository root instead of prepending. The test harness prepends
    # the concrete service directory to ``sys.path`` before imports. If we
    # inserted the repo root at index 0 it would become the first entry,
    # causing our service‑detection logic (which looks at ``sys.path[0]``) to
    # mis‑identify the active service. By appending we keep the service
    # directory at the front while still making the repo root available for
    # top‑level namespace packages such as ``services`` and ``common``.
    sys.path.append(_repo_root)

# ---------------------------------------------------------------------------
# 2. Add each service's ``app`` directory to ``sys.path`` (append).
# ---------------------------------------------------------------------------
# Adding these directories ensures that the ``app`` namespace package can locate
# every service's ``app`` subpackage via ``pkgutil.extend_path``.  They are
# appended because the test harness may later *prepend* the specific service
# directory, which should take precedence.
try:
    from pathlib import Path

    services_root = Path(__file__).resolve().parents[1] / "services"
    for svc_dir in services_root.iterdir():
        app_dir = svc_dir / "app"
        if app_dir.is_dir():
            sp = str(app_dir)
            if sp not in sys.path:
                sys.path.append(sp)
except Exception:
    pass

# ---------------------------------------------------------------------------
# 2. Pre‑import the top‑level ``services`` namespace package.
# ---------------------------------------------------------------------------
# By importing ``services`` now (after the repository root has been placed at the
# front of ``sys.path``) we ensure the module object is created from the repo‑wide
# package directory.  Subsequent additions of a service directory to ``sys.path``
# (performed by the test harness) will not replace this already‑loaded module,
# preventing the shadowing issue where ``services`` from a service directory
# would be imported instead of the shared namespace.
try:
    import services  # noqa: F401
except Exception:
    # If the import fails for any reason we simply continue; the later imports
    # will raise a clear error.
    pass

# ---------------------------------------------------------------------------
# 3. If the current working directory is inside a service directory, prepend
#    that service's ``app`` path so that ``import app`` resolves to the correct
#    implementation for tests that rely on a plain ``app`` import (e.g.
#    ``services/constitution-service`` tests).
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 3. Prioritize the service whose directory is first on ``sys.path``.
# ---------------------------------------------------------------------------
# The test harness prepends the *service* directory (e.g. ``.../services/identity-service``)
# to ``sys.path`` before importing ``app`` modules.  We locate that directory and
# ensure its ``app`` subpackage appears first in the ``app`` namespace ``__path__``.
try:
    first_path = sys.path[0]
    services_root = Path(__file__).resolve().parents[1] / "services"
    first_path_obj = Path(first_path)
    # Check if the first entry is a service directory.
    for svc_dir in services_root.iterdir():
        if first_path_obj.samefile(svc_dir):
            svc_app = svc_dir / "app"
            if svc_app.is_dir():
                sp = str(svc_app)
                # Ensure the service app directory is on sys.path (it may already be).
                if sp not in sys.path:
                    sys.path.insert(0, sp)
                # Reorder the top‑level ``app`` namespace.
                # NOTE: Previously we attempted to import the top‑level ``app`` package
                # here and manually reorder its ``__path__``.  That import occurs during
                # interpreter start‑up, *before* the pytest harness prepends the concrete
                # service directory to ``sys.path``.  As a result the ``app`` package was
                # initialised with the wrong (repo‑root) path ordering, causing imports
                # like ``app.core.constitution`` to resolve to the wrong service and
                # raise ``ModuleNotFoundError``.  We now rely on the lazy detection logic
                # in ``app/__init__.py`` which runs **after** the test harness has
                # modified ``sys.path``.  Therefore the eager import and path manipulation
                # have been removed.
            break
except Exception:
    # If anything goes wrong we silently continue – the import system will fall
    # back to the default ordering.
    pass

# ---------------------------------------------------------------------------
# 3. No longer pre‑populate the top‑level ``app`` namespace.
# ---------------------------------------------------------------------------
# The test harness prepends the specific service directory to ``sys.path``
# before importing ``app`` modules (e.g., ``app.core.constitution``).  By keeping
# the ``app`` namespace package empty aside from ``pkgutil.extend_path`` we allow
# Python's normal import machinery to resolve ``app`` to the service directory
# that appears first on ``sys.path``.  This avoids cross‑service submodule
# collisions such as ``app.core`` from different services.

# The test harness already prepends the individual service directory to
# ``sys.path`` before importing the service's ``app`` package.  With the
# repository root now at the front of ``sys.path`` (see above), the top‑level
# ``app`` namespace package defined at the repository root is discoverable, and
# the service‑specific ``app`` subpackage will be resolved correctly via the
# service directory already present at index 0.  No additional path manipulation
# is required here.

def _patch_redis_container() -> None:
    """Ensure ``RedisContainer`` provides ``get_connection_url``.

    Some environments ship an older ``testcontainers`` version where the
    ``RedisContainer`` class lacks the ``get_connection_url`` helper required
    by the identity‑service tests.  We import the class explicitly and assign a
    compatible implementation unconditionally – this works even if the method
    already exists (it will simply be overwritten with an equivalent version).
    """
    try:
        module = importlib.import_module("testcontainers.redis")
        RedisContainer = getattr(module, "RedisContainer", None)
        if RedisContainer is None:
            return
        def get_connection_url(self):  # type: ignore[override]
            host = self.get_container_host_ip()
            port = self.get_exposed_port("6379/tcp")
            return f"redis://{host}:{port}"
        setattr(RedisContainer, "get_connection_url", get_connection_url)
        # Debug: confirm method presence after patch
        print('DEBUG: after patch, hasattr(RedisContainer, "get_connection_url") =',
              hasattr(RedisContainer, "get_connection_url"))
    except Exception as e:
        print('DEBUG: _patch_redis_container exception:', e)

_patch_redis_container()

# Debug: print sys.path after sitecustomize modifications
print('>>> sitecustomize final sys.path:', sys.path[:5])
