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
import pathlib
import sys

# ---------------------------------------------------------------------
# Namespace package handling
# ---------------------------------------------------------------------
# ``services`` is a namespace package that is split across many sub‑folders.
# ``pkgutil.extend_path`` merges the ``services`` directories found in each
# service with the top‑level ``services`` package.
__path__ = pkgutil.extend_path(__path__, __name__)

# ---------------------------------------------------------------------
# Ensure the repository root is on ``sys.path``
# ---------------------------------------------------------------------
# Tests prepend the individual service directory (e.g. ``services/jobs``) to
# ``sys.path`` which hides the repository root.  Many services import the
# shared ``common`` package (e.g. ``common.config.runtime``).  Adding the repo
# root here makes those imports succeed without needing a separate shim in
# each service.
# The repository root is needed for top‑level namespace packages such as
# ``common``.  Previously we inserted it at the *front* of ``sys.path`` which
# caused the repository root to shadow the service‑specific directories that
# pytest prepends (e.g. ``services/analytics-service``).  As a result imports
# like ``app.core.constitution`` resolved to a non‑existent top‑level ``app``
# package, leading to ``ModuleNotFoundError`` for many services.
#
# By **appending** the repository root we keep the service directory as the
# first entry (the order pytest expects) while still making shared namespace
# packages discoverable.
repo_root = pathlib.Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
	# Append the repository root so that the service directory (which the test
	# harness prepends) stays first in ``sys.path``.  This preserves the expected
	# import order for service‑local modules (e.g. ``app``) while still making
	# top‑level packages like ``common`` discoverable.
	sys.path.append(str(repo_root))
