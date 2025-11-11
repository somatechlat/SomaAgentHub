"""Secrets loader with explicit error handling (no silent bypass)."""

import logging
from services.common.config.base_settings import resolve_env


logger = logging.getLogger("gateway.secrets")


def load_secret(
    env_var: str, file_env: str | None = None, default: str | None = None
) -> str | None:
    """Load a secret from environment variable or file.

    - Returns the env var if set.
    - If a file env is provided and points to a readable file, returns its trimmed content.
    - On file errors, logs and returns the provided default (or None if unspecified).
    """
    # Prefer environment variable first
    value = resolve_env(env_var)
    if value:
        return value

    # Try file path from file_env
    if file_env:
        file_path = resolve_env(file_env)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    return f.read().strip()
            except Exception as exc:
                logger.error("Failed to read secret file %s: %s", file_path, exc)

    # Fall back to default (explicit), otherwise None
    if default is not None:
        return default
    return None
