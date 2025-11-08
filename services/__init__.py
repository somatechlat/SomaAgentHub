"""Top‑level **namespace** package for all SomaAgentHub services.

The repository contains many independent FastAPI services under the
``services/`` directory (e.g. ``analytics-service``, ``jobs``, ``identity-service``).
Tests prepend the *service* directory to ``sys.path`` (e.g. ``.../services/jobs``)
and then import ``services.jobs.app.main``.  To make that import succeed we
expose a *namespace package* named ``services`` that can be split across the
different service directories.

Using :pyfunc:`pkgutil.extend_path` merges the ``services`` package found in
each service folder with the one at the repository root, allowing Python to
resolve ``services.<service>`` regardless of which directory appears first on
``sys.path``.
"""

import pkgutil

# ---------------------------------------------------------------------
# Namespace package handling
# ---------------------------------------------------------------------
# ``services`` is a namespace package that is split across many sub‑folders.
# ``pkgutil.extend_path`` merges the ``services`` directories found in each
# service with the top‑level ``services`` package.
__path__ = pkgutil.extend_path(__path__, __name__)

# ---------------------------------------------------------------------
# Repository‑wide import‑path handling
# ---------------------------------------------------------------------
# The import‑path shim is now centralized in ``services/_path_setup.py``.
# Individual services import that helper from their ``app/__init__`` modules.
# Keeping this file free of ``sys.path`` manipulation avoids duplicate logic
# and ensures a single source of truth for path handling.
