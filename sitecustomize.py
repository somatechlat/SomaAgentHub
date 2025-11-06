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

# ---------------------------------------------------------------------------
# 1. Add repository root to ``sys.path``
# ---------------------------------------------------------------------------
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    # Append the repository root to ``sys.path`` rather than inserting at the
    # front.  Test harnesses prepend the individual service directory (e.g.
    # ``services/constitution-service``) to ``sys.path`` before imports.  By
    # appending we keep that service‑specific path ahead of the repository
    # root, allowing imports like ``import app.core.constitution`` to resolve to
    # the service‑local ``app`` package.  The repository root is still added so
    # that top‑level namespace packages such as ``common`` are discoverable.
    sys.path.append(_repo_root)

def _patch_redis_container() -> None:
    """Add ``get_connection_url`` to ``RedisContainer`` if missing.

    The method returns a ``redis://host:port`` URL constructed from the container
    host IP and the exposed Redis port (default ``6379/tcp``).  This mirrors the
    behaviour of newer ``testcontainers`` releases.
    """
    try:
        module = importlib.import_module("testcontainers.redis")
        RedisContainer = getattr(module, "RedisContainer", None)
        if RedisContainer is None:
            return
        if not hasattr(RedisContainer, "get_connection_url"):
            def get_connection_url(self):  # type: ignore[override]
                host = self.get_container_host_ip()
                port = self.get_exposed_port("6379/tcp")
                return f"redis://{host}:{port}"

            RedisContainer.get_connection_url = get_connection_url  # type: ignore[attr-defined]
    except Exception:
        pass

_patch_redis_container()
