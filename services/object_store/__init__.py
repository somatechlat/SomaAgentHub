from services.common.config.base_settings import resolve_env
"""Canonical object store package.

The implementation now lives directly under ``services.object_store``.
Imports such as ``from services.object_store.app.client import ObjectStoreClient``
are supported without aliasing.
"""

