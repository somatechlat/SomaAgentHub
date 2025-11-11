"""DEPRECATED: deployment_strategy removed.

Use direct environment variables via `resolve_env` in `base_settings`.
Importing this module raises to prevent accidental usage.
"""

raise ImportError(
    "services.common.deployment.deployment_strategy is deprecated. "
    "Use direct env vars with SOMA_AGENT_HUB_ prefix and resolve_env."
)