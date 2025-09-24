"""Secret loading utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

__all__ = ["load_secret"]


def load_secret(env_name: str, *, file_env: Optional[str] = None, default: Optional[str] = None) -> Optional[str]:
    """Load a secret from environment or file.

    Parameters
    ----------
    env_name: str
        Environment variable containing the secret directly.
    file_env: Optional[str]
        Environment variable pointing to a file containing the secret.
    default: Optional[str]
        Value to return if neither environment variable is set.
    """

    value = os.getenv(env_name)
    if value:
        return value
    if file_env:
        path_value = os.getenv(file_env)
        if path_value and Path(path_value).exists():
            return Path(path_value).read_text().strip()
    return default
