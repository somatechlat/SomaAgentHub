"""Alias package for the hyphenated ``capsule-repo`` directory.

Python identifiers cannot contain hyphens, so the repository uses a directory
named ``capsule-repo`` for the service implementation.  To allow import
statements such as ``import services.capsule_repo.app.main`` we provide this
shim that simply re‑exports the module tree from the real directory.
"""

from importlib import import_module
import sys
import pathlib

# Resolve the absolute path of the sibling ``capsule-repo`` package.
_pkg_path = pathlib.Path(__file__).resolve().parent.parent / "capsule-repo"
if _pkg_path.is_dir():
    # Insert the hyphenated package into ``sys.modules`` under the expected
    # name so that attribute access works transparently.
    sys.modules[__name__ + ".app"] = import_module("services.capsule-repo.app")
else:
    raise ImportError("Unable to locate the 'capsule-repo' package directory")

# Export the submodule namespace for static analysis tools.
__all__ = ["app"]
