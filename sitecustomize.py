"""Site customization for test environment.

This module is automatically imported by Python when ``site`` is loaded (if a
``sitecustomize.py`` file is found on ``sys.path``).  The repository root is
added to ``PYTHONPATH`` during testing, so this file is executed before the
project's test suite runs.

The purpose of this file is to patch the ``testcontainers`` ``RedisContainer``
class, which in some versions does not provide a ``get_connection_url`` helper
method expected by the identity‑service tests.  Adding the method here avoids
modifying the upstream library or the test code.
"""

import importlib

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
