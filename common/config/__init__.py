"""Namespace package for ``common.config``.

Provides a package marker so imports like ``common.config.runtime`` work when
the repository root is on ``sys.path`` (which our ``services/__init__`` shim
ensures). No additional code is required.
"""