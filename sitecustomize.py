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
import logging
import os
import sys
from pathlib import Path

# Debug: indicate that sitecustomize has been loaded (appears in pytest output)
_logger = logging.getLogger("sitecustomize")
_logger.debug("sitecustomize loaded")

# ---------------------------------------------------------------------------
# 1. Ensure the repository root is on ``sys.path``.
# ---------------------------------------------------------------------------
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    # Prepend the repository root so that top‑level namespace packages such as
    # ``services`` and ``common`` are available.  Individual service ``app``
    # directories will be placed before this entry when detected (see step 3).
    sys.path.insert(0, _repo_root)

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
try:
    cwd = Path.cwd().resolve()
    services_root = Path(__file__).resolve().parents[1] / "services"
    for svc_dir in services_root.iterdir():
        if cwd.is_relative_to(svc_dir):
            svc_app = svc_dir / "app"
            if svc_app.is_dir():
                sp = str(svc_app)
                if sp not in sys.path:
                    # Prepend to give this service priority.
                    sys.path.insert(0, sp)
            break
except Exception:
    # ``Path.is_relative_to`` is available in Python 3.9+. If unavailable, ignore.
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
        _logger.debug(
            'after patch, hasattr(RedisContainer, "get_connection_url") = %s',
            hasattr(RedisContainer, "get_connection_url"),
        )
    except Exception as e:
        _logger.debug("_patch_redis_container exception: %s", e)


_patch_redis_container()
