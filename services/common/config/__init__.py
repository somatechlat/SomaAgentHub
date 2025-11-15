"""Unified Configuration System for SomaAgentHub

This module provides a centralized configuration management system that replaces
the multiple overlapping configuration patterns found throughout the codebase.

All services should import configuration from this module:
    from services.common.config import get_config, get_settings

The system provides:
- Single source of truth for all configuration
- Environment variable resolution with standardized prefix
- Service-specific configuration extensions
- Type-safe configuration with validation
- Development and production mode support
"""

from .base_config import BaseConfig, DeploymentMode, ResourceProfile
from .service_config import ServiceConfig, get_service_config
from .env_resolver import resolve_env, get_env_var
from .settings import get_settings, settings

__all__ = [
    "BaseConfig",
    "DeploymentMode", 
    "ResourceProfile",
    "ServiceConfig",
    "get_service_config",
    "resolve_env",
    "get_env_var",
    "get_settings",
    "settings",
]