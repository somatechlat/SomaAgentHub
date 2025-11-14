"""Centralised configuration for the entire SomaAgentHub codebase.

All services should import the ``settings`` singleton from this module:

from services.common.config.settings import settings

The underlying ``BaseServiceSettings`` (defined in ``base_settings.py``) reads
environment variables using the canonical ``SOMA_AGENT_HUB_`` prefix via the
``resolve_env`` helper.  This file provides a single source of truth – there are
no per‑service config wrappers, no backup files, and no legacy ``SOMA_AGENT_HUB_``
or ``SOMA_AGENT_HUB_`` prefixes.
"""

from __future__ import annotations

from functools import lru_cache

from services.common.config.base_settings import BaseServiceSettings, load_settings, resolve_env


# Backwards-compatible helpers
@lru_cache()
def get_settings() -> BaseServiceSettings:
	"""Return the cached `BaseServiceSettings` instance for the process.

	Services should call `get_settings()` to obtain configuration rather than
	constructing settings directly. This avoids duplicated parsing and keeps
	runtime behavior consistent across the project.
	"""
	return load_settings(BaseServiceSettings)


# Convenience export used across the codebase
settings = get_settings()


# Backwards compatibility names
CommonSettings = BaseServiceSettings


def get_common_settings() -> BaseServiceSettings:
	return get_settings()


__all__ = ["settings", "get_settings", "get_common_settings", "CommonSettings", "resolve_env"]
