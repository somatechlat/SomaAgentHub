"""Entry point for policy engine service.

This module simply re-exports the application defined in :mod:`policy_app`
so ``uvicorn app.main:app`` uses the fully featured service implementation.
"""

from .policy_app import app  # noqa: F401