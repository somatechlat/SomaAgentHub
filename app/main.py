"""Top‑level ``app.main`` shim.

The test suite imports ``app.main`` (or ``from app.main import create_app``)
directly, regardless of which service is being exercised. Because the
repository contains many independent services, each with its own ``app``
package, a plain import would resolve to the *first* ``app`` module that was
imported – typically the one from the analytics service. That leads to the
``ImportError: cannot import name 'create_app'`` failures seen in the test run.

This shim dynamically forwards the import to the service‑specific ``app.main``
module based on the current working directory (or the first entry on
``sys.path`` that points inside ``services/<service>-service``). It then
re‑exports the public attributes (``app`` FastAPI instance and ``create_app``
factory) so that the tests see the correct objects for the service they are
testing.
"""

from __future__ import annotations

import importlib
import pathlib
import sys
from types import ModuleType


def _detect_service_name() -> str | None:
    """Detect the service name using import stack introspection.

    The original approach relied on ``sys.path[0]`` which is ``''`` (the current
    working directory) when the test runner starts, causing the shim to be
    unable to determine the active service.  We now walk the call stack
    (``inspect.stack``) looking for a filename that resides under a
    ``services/<service-name>`` directory. The first match wins and provides the
    service name.
    """
    import inspect

    # 1. Inspect the call stack for a file inside a service directory.
    for frame in inspect.stack():
        path = pathlib.Path(frame.filename).resolve()
        # Walk up the path hierarchy looking for a ``services`` parent.
        for parent in path.parents:
            if parent.name == "services":
                # The immediate child of ``services`` is the service directory.
                try:
                    svc = path.relative_to(parent).parts[0]
                    return svc
                except Exception:
                    continue

    # 2. Fallback to the original heuristics (sys.path[0] or cwd).
    if sys.path:
        first = pathlib.Path(sys.path[0])
        if first.is_dir() and first.parent.name == "services":
            return first.name
    cwd = pathlib.Path.cwd().resolve()
    for parent in cwd.parents:
        if parent.name == "services":
            for child in parent.iterdir():
                try:
                    if cwd.is_relative_to(child):
                        return child.name
                except AttributeError:
                    if str(cwd).startswith(str(child)):
                        return child.name
    return None


def _load_service_main() -> ModuleType:
    """Import the concrete ``services.<svc>.app.main`` module.

    Raises ``ImportError`` if the service cannot be determined.
    """
    svc = _detect_service_name()
    if not svc:
        raise ImportError("Unable to detect service for top‑level app.main shim")
    module_path = f"services.{svc}.app.main"
    return importlib.import_module(module_path)


# Load the concrete module once and re‑export its public symbols.
_service_main = _load_service_main()

for _name in dir(_service_main):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_service_main, _name)

# Explicitly define ``__all__`` for static analysis tools.
__all__ = [n for n in globals() if not n.startswith("_")]
