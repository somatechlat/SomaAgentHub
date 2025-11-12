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

from services.common.config.base_settings import BaseServiceSettings, load_settings
from services.common.config.base_settings import resolve_env

# The ``settings`` instance is cached (lru_cache) inside ``load_settings`` so it
# is created only once per process and can be safely imported from anywhere.
settings = load_settings(BaseServiceSettings)

__all__ = ["settings"]
