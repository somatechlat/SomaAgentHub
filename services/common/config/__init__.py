"""Unified Configuration System for SomaAgentHub

This module provides a centralized configuration management system that replaces
multiple overlapping configuration patterns found throughout the codebase.

All services should import configuration from this module:
    from services.common.config import get_config, get_settings

The system provides:
    - Single source of truth for all configuration
    - Environment variable resolution with standardized prefix
    - Service-specific configuration extensions
    - Type-safe configuration with validation
    - Development and production mode support
"""

from .base_config import BaseConfig, DeploymentMode, ResourceProfile, get_config
from .env_resolver import get_env_var, resolve_env
from .service_config import ServiceConfig, get_service_config
from .settings import get_settings, settings


# -------------------------------------------------------------------------
# Helper for service‑specific configuration
# -------------------------------------------------------------------------
def get_service_settings(service_name: str):
    """Return a ``BaseConfig`` instance scoped to *service_name*.

    The central ``BaseConfig`` reads environment variables with the
    ``SOMA_AGENT_HUB_`` prefix.  For service‑specific values we simply set the
    ``service_name`` attribute after loading the global configuration.  This
    mirrors the historic pattern where each service had its own ``config.py``
    that defined ``SERVICE_NAME`` and ``SERVICE_PORT``.

    The function is cached via ``functools.lru_cache`` to avoid repeated
    parsing of environment variables.
    """

    from functools import lru_cache

    @lru_cache(maxsize=32)
    def _load() -> BaseConfig:
        cfg = get_config()
        # ``BaseConfig`` is mutable; we create a shallow copy so mutating the
        # ``service_name`` does not affect the global singleton.
        cfg_copy = cfg.__class__(**cfg.dict())
        cfg_copy.service_name = service_name
        return cfg_copy

    return _load()


__all__ = [
    "BaseConfig",
    "DeploymentMode",
    "ResourceProfile",
    "ServiceConfig",
    "get_config",
    "get_env_var",
    "get_service_config",
    "get_service_settings",
    "get_settings",
    "resolve_env",
    "settings",
]
