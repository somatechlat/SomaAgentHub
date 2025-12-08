"""Environment Variable Resolution Utilities

Provides centralized environment variable resolution with standardized
prefixing and fallback values for the entire SomaAgentHub platform.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

# Standardized environment variable prefix
ENV_PREFIX = "SOMA_AGENT_HUB_"


@lru_cache(maxsize=128)
def resolve_env(name: str, default: Any = None, prefix: str = ENV_PREFIX) -> Any:
    """Resolve an environment variable with standardized prefix.

    This is the single source of truth for environment variable resolution
    across the entire SomaAgentHub platform. It replaces the multiple
    overlapping resolution patterns found throughout the codebase.

    Args:
        name: Environment variable name (without prefix)
        default: Default value if variable is not found
        prefix: Environment variable prefix (defaults to SOMA_AGENT_HUB_)

    Returns:
        The resolved environment variable value or default

    Examples:
        >>> resolve_env("DATABASE_URL")
        "postgresql://postgres:postgres@localhost:5432/soma"

        >>> resolve_env("DEBUG", "false")
        "true"

        >>> resolve_env("CUSTOM_SETTING", prefix="CUSTOM_")
        "custom_value"
    """
    if prefix:
        full_name = f"{prefix}{name}"
    else:
        full_name = name

    # First try the prefixed version
    value = os.environ.get(full_name)
    if value is not None:
        return value

    # For backwards compatibility, try without prefix if prefixed version not found
    if prefix and prefix != "":
        value = os.environ.get(name)
        if value is not None:
            return value

    # Return default if not found
    return default


def get_env_var(name: str, default: Any = None, required: bool = False) -> Any:
    """Get an environment variable with optional required validation.

    This is a simpler interface for common environment variable access.

    Args:
        name: Environment variable name
        default: Default value if not found
        required: If True, raises ValueError when variable is not found

    Returns:
        The environment variable value

    Raises:
        ValueError: If required=True and variable is not found

    Examples:
        >>> get_env_var("DATABASE_URL", required=True)
        "postgresql://postgres:postgres@localhost:5432/soma"

        >>> get_env_var("DEBUG", "false")
        "false"
    """
    value = resolve_env(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


def get_bool_env(name: str, default: bool = False) -> bool:
    """Get a boolean environment variable.

    Args:
        name: Environment variable name
        default: Default boolean value

    Returns:
        Boolean value parsed from environment variable

    Examples:
        >>> get_bool_env("DEBUG", False)
        True

        >>> get_bool_env("ENABLE_METRICS", True)
        False
    """
    value = resolve_env(name, str(default))
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on", "enabled")

    return bool(value)


def get_int_env(name: str, default: int = 0) -> int:
    """Get an integer environment variable.

    Args:
        name: Environment variable name
        default: Default integer value

    Returns:
        Integer value parsed from environment variable

    Examples:
        >>> get_int_env("PORT", 8000)
        8080

        >>> get_int_env("MAX_CONNECTIONS", 10)
        100
    """
    value = resolve_env(name, str(default))
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_float_env(name: str, default: float = 0.0) -> float:
    """Get a float environment variable.

    Args:
        name: Environment variable name
        default: Default float value

    Returns:
        Float value parsed from environment variable

    Examples:
        >>> get_float_env("TIMEOUT", 30.0)
        60.5
    """
    value = resolve_env(name, str(default))
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_list_env(
    name: str, default: list[str] = None, separator: str = ","
) -> list[str]:
    """Get a list environment variable.

    Args:
        name: Environment variable name
        default: Default list value
        separator: List separator character

    Returns:
        List of strings parsed from environment variable

    Examples:
        >>> get_list_env("CORS_ORIGINS", ["*"])
        ["http://localhost:3000", "https://example.com"]

        >>> get_list_env("KAFKA_BOOTSTRAP_SERVERS", ["localhost:9092"])
        ["kafka1:9092", "kafka2:9092"]
    """
    if default is None:
        default = []

    value = resolve_env(name)
    if value is None:
        return default

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        items = [item.strip() for item in value.split(separator) if item.strip()]
        return items

    return default


def get_dict_env(name: str, default: dict[str, Any] = None) -> dict[str, Any]:
    """Get a dictionary environment variable from JSON string.

    Args:
        name: Environment variable name
        default: Default dictionary value

    Returns:
        Dictionary parsed from JSON environment variable

    Examples:
        >>> get_dict_env("FEATURE_FLAGS", {"new_ui": False})
        {"new_ui": True, "experimental": False}
    """
    if default is None:
        default = {}

    value = resolve_env(name)
    if value is None:
        return default

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            import json

            return json.loads(value)
        except json.JSONDecodeError:
            return default

    return default


def get_service_url(service_name: str, default_port: int = 8000) -> str:
    """Get a service URL from environment variables.

    This provides a standardized way to construct service URLs for
    inter-service communication.

    Args:
        service_name: Name of the service (e.g., "orchestrator")
        default_port: Default port for the service

    Returns:
        Service URL string

    Examples:
        >>> get_service_url("orchestrator", 10001)
        "http://orchestrator:10001"

        >>> get_service_url("identity-service", 10002)
        "http://identity-service:10002"
    """
    # Try service-specific URL first
    service_url = resolve_env(f"{service_name.upper()}_URL")
    if service_url:
        return service_url

    # Try port override
    port = get_int_env(f"{service_name.upper()}_PORT", default_port)

    # Get service host (default to service name)
    host = resolve_env(f"{service_name.upper()}_HOST", service_name)

    return f"http://{host}:{port}"


def get_database_url(service_name: str = None) -> str:
    """Get database URL with service-specific fallback.

    Args:
        service_name: Optional service name for service-specific database

    Returns:
        Database URL string

    Examples:
        >>> get_database_url()
        "postgresql://postgres:postgres@localhost:5432/soma"

        >>> get_database_url("orchestrator")
        "postgresql://postgres:postgres@localhost:5432/orchestrator"
    """
    # Try service-specific database URL first
    if service_name:
        service_db_url = resolve_env(f"{service_name.upper()}_DATABASE_URL")
        if service_db_url:
            return service_db_url

    # Try global database URL
    global_db_url = resolve_env("DATABASE_URL")
    if global_db_url:
        return global_db_url

    # Default development URL
    return "postgresql://postgres:postgres@localhost:5432/soma"


def get_redis_url(service_name: str = None) -> str:
    """Get Redis URL with service-specific fallback.

    Args:
        service_name: Optional service name for service-specific Redis

    Returns:
        Redis URL string

    Examples:
        >>> get_redis_url()
        "redis://localhost:6379/0"

        >>> get_redis_url("orchestrator")
        "redis://localhost:6379/1"
    """
    # Try service-specific Redis URL first
    if service_name:
        service_redis_url = resolve_env(f"{service_name.upper()}_REDIS_URL")
        if service_redis_url:
            return service_redis_url

    # Try global Redis URL
    global_redis_url = resolve_env("REDIS_URL")
    if global_redis_url:
        return global_redis_url

    # Default development URL
    return "redis://localhost:6379/0"


def clear_env_cache() -> None:
    """Clear the environment variable resolution cache.

    This is useful for testing or when environment variables change
    during runtime and you need to force re-resolution.
    """
    resolve_env.cache_clear()


def get_all_env_vars(prefix: str = ENV_PREFIX) -> dict[str, str]:
    """Get all environment variables with the specified prefix.

    Args:
        prefix: Environment variable prefix to filter by

    Returns:
        Dictionary of environment variables with the prefix

    Examples:
        >>> get_all_env_vars("SOMA_AGENT_HUB_")
        {"DATABASE_URL": "...", "DEBUG": "true", ...}
    """
    env_vars = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix from key
            clean_key = key[len(prefix) :]
            env_vars[clean_key] = value
    return env_vars


def validate_required_env_vars(required_vars: list[str]) -> list[str]:
    """Validate that all required environment variables are set.

    Args:
        required_vars: List of required environment variable names

    Returns:
        List of missing environment variables (empty if all present)

    Examples:
        >>> validate_required_env_vars(["DATABASE_URL", "JWT_SECRET"])
        []

        >>> validate_required_env_vars(["MISSING_VAR"])
        ["MISSING_VAR"]
    """
    missing_vars = []
    for var_name in required_vars:
        value = resolve_env(var_name)
        if value is None:
            missing_vars.append(var_name)
    return missing_vars
