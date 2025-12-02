entralised configuration for the entire SomaAgentHub codebase.

services should import the ``settings`` singleton from this module:

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


    ckwards-compatible helpers
    @lru_cache()
    def get_settings() -> BaseServiceSettings:
        Return the cached `BaseServiceSettings` instance for the process.

        vices should call `get_settings()` to obtain configuration rather than
        structing settings directly. This avoids duplicated parsing and keeps
        time behavior consistent across the project.

        urn load_settings(BaseServiceSettings)


        nvenience export used across the codebase
        tings = get_settings()


        ckwards compatibility names
        monSettings = BaseServiceSettings


 get_common_settings() -> BaseServiceSettings:
     urn get_settings()


     ll__ = ["settings", "get_settings", "get_common_settings", "CommonSettings", "resolve_env"]
