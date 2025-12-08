"""Strict secret loader.

All secret values must be provided via the canonical ``SOMA_AGENT_HUB_``
silencing of missing secrets are allowed. If a secret cannot be resolved the
function raises a ``RuntimeError`` to fail fast and surface the configuration
issue.
"""

import logging

from services.common.config.base_settings import resolve_env

logger = logging.getLogger("gateway.secrets")


def load_secret(env_var: str) -> str:
    """Load a secret strictly from an environment variable.

    Args:
        env_var: The canonical ``SOMA_AGENT_HUB_`` variable name.

    Returns:
        The secret value.

    Raises:
        RuntimeError: If the variable is not set.
    """
    value = resolve_env(env_var)
    if not value:
        raise RuntimeError(f"Required secret '{env_var}' is not set in the environment")
    return value
