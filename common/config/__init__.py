from services.common.config.base_settings import resolve_env
"""Namespace package for ``common.config``.

Provides a package marker so imports like ``common.config.runtime`` work when
the repository root is on ``sys.path`` (which our ``services/__init__`` shim
ensures). No additional code is required.
"""
