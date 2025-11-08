"""Simple replacement for somagent_secrets module."""

import os


def load_secret(
    env_var: str, file_env: str | None = None, default: str | None = None
) -> str | None:
    """Load a secret from environment variable or file."""
    # Try environment variable first
    value = os.getenv(env_var)
    if value:
        return value

    # Try file path from file_env
    if file_env:
        file_path = os.getenv(file_env)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    return f.read().strip()
            except Exception:
                pass

    # Return default
    return default
