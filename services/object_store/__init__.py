"""Alias package for the hyphenated ``services/object-store`` directory.

The repository stores the object‑store client implementation in a folder named
``services/object-store`` (note the hyphen).  Python module names cannot contain
hyphens, so importing ``services.object-store`` raises a ``SyntaxError``.  To
provide a valid import path we expose an *alias* package ``services.object_store``
that extends its ``__path__`` to include the original hyphenated directory.

Usage example::

    from services.object_store.app.client import ObjectStoreClient

This file makes the above import work without moving or renaming the existing
code.
"""

import pathlib
import pkgutil

# Resolve the sibling directory that actually contains the implementation.
_repo_root = pathlib.Path(__file__).resolve().parent.parent
_hyphen_dir = _repo_root / "object-store"

if _hyphen_dir.is_dir():
    # Extend the namespace path so that imports under ``services.object_store``
    # resolve to modules inside the hyphenated folder.
    __path__ = pkgutil.extend_path([str(_hyphen_dir)], __name__)
