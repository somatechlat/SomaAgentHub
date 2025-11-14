"""Compatibility shim for tests expecting the underscore package name.

This package maps the dotted name ``services.task_capsule_repo`` to the
existing directory ``services/task-capsule-repo`` (which cannot be imported
using an underscore due to the hyphen). It does so by inserting the real
service directory into the package's ``__path__`` so Python can find the
submodules as expected by the test suite.
"""

from __future__ import annotations

import pathlib
import sys

# Resolve the sibling directory with a hyphen in its name.
_this_dir = pathlib.Path(__file__).resolve().parent
_real_service = _this_dir / ".." / "task-capsule-repo"
_real_service = _real_service.resolve()

if str(_real_service) not in __path__:
    __path__.insert(0, str(_real_service))
