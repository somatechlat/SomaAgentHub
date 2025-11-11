from services.common.config.base_settings import resolve_env

"""DEPRECATED: session_manager has been removed.

Use service-local session handling with `resolve_env` and standard JWT libs.
Importing this module raises to prevent accidental usage.
"""

raise ImportError(
    "services.common.session.session_manager is deprecated. "
    "Use service-local JWT handling and resolve_env for configuration."
)
