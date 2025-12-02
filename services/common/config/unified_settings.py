"""DEPRECATED: unified_settings has been removed.

Use `services.common.config.base_settings.resolve_env` and service-specific settings.
This module intentionally raises to prevent accidental usage.
"""

raise ImportError(
    "services.common.config.unified_settings is deprecated. "
    "Use services.common.config.base_settings.resolve_env and canonical settings."
)
