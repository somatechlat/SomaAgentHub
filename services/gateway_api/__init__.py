"""Namespace shim for the legacy ``services/gateway-api`` directory.

The on‑disk directory is named ``gateway-api`` (containing a hyphen), which
cannot be used in a Python import statement. The codebase therefore imports
the package using the underscore variant ``services.gateway_api``. To make that
import resolve to the actual files, we extend the package ``__path__`` to also
include the sibling ``gateway-api`` directory.

This approach mirrors the ``services`` top‑level namespace handling and
requires no manual module loading – standard import machinery will locate the
submodules (e.g. ``services.gateway_api.app.core.config``) inside the hyphen‑
named folder.
"""

from __future__ import annotations

import pkgutil
import pathlib
import sys

# Extend the package path to include the sibling ``gateway-api`` directory.
_this_dir = pathlib.Path(__file__).resolve().parent
_sibling = _this_dir.parent / "gateway-api"
if _sibling.is_dir():
# ``extend_path`` merges any existing namespace packages.
__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[assignment]
__path__.append(str(_sibling))

# Export a placeholder ``app`` attribute for completeness; actual submodules
# will be imported lazily by Python when accessed.
app = sys.modules.get("services.gateway_api.app")
