from services.common.config.base_settings import resolve_env

"""DEPRECATED: Service Registry Pattern

This module is deprecated. Use explicit service URLs resolved via
`services.common.config.base_settings.resolve_env` and keep dependencies
simple. Importing this module will raise to prevent accidental usage.
"""
raise ImportError(
"services.common.registry.service_registry is deprecated and disabled. "
"Use explicit service URLs via resolve_env."
)
