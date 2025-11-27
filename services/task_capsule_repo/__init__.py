"""Shim package for the Task Capsule Repository.

The production implementation resides in the sibling directory
``task-capsule-repo`` (which contains a hyphen and cannot be imported via the
``services.task_capsule_repo`` dotted name). For the Sprint 1 test suite we
provide a minimal pure‑Python implementation located in the ``app`` submodule
of this package. This file simply re‑exports that ``app`` package so that
imports such as ``services.task_capsule_repo.app`` work correctly.
"""

# Export the minimal implementation used by the tests.
from . import app  # noqa: F401
