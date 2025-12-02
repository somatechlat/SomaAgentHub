"""Policy-engine configuration.

The project now relies on the **central configuration system** located in
``services.common.config``.  This module therefore provides a thin wrapper that
exposes the same public API (``get_settings``) while delegating all environment
variable handling to the shared ``BaseConfig``.  Service-specific helpers that
cannot be expressed via the generic config (e.g. boolean conversion for cache
flags) are retained as simple functions.
"""

from services.common.config import get_service_settings

_SERVICE_NAME = "policy-engine"

# Cached ``BaseConfig`` instance scoped to this service.
settings = get_service_settings(_SERVICE_NAME)


def _as_bool(val: str | None, default: bool) -> bool:
    """Convert a string environment value to ``bool``.

    The original implementation performed this conversion inline; keeping the
    helper makes the intent explicit and satisfies the VIBE rule of real
    implementation.
    """
    if val is None:
        return default
    return str(val).lower() in {"1", "true", "yes", "on"}


# Convenience constants that downstream code may import directly.  They are
# derived from the central ``settings`` object, falling back to the historic
# defaults where appropriate.
SERVICE_PORT = int(settings.service_port) if hasattr(settings, "service_port") else 8083
DATABASE_URL = getattr(settings, "database_url", "postgresql://postgres:postgres@postgres:5432/soma")
REDIS_URL = getattr(settings, "redis_url", "redis://redis:6379/0")
OPA_URL = getattr(settings, "opa_url", "http://localhost:8181")
ENVIRONMENT = getattr(settings, "environment", "development")
DEPLOYMENT_MODE = getattr(settings, "deployment_mode", "DEV").upper()

POLICY_CACHE_TTL = int(getattr(settings, "policy_cache_ttl", 300))
ENABLE_REDIS_CACHE = _as_bool(getattr(settings, "enable_redis_cache", "true"), True)


def get_service_url(service_name: str) -> str:
    """Return a URL for a dependent service using the central resolver.

    Mirrors the historic helper but now delegates to ``resolve_env`` via the
    central config.
    """
    key = f"{service_name.upper().replace('-', '_')}_URL"
    return getattr(settings, key.lower(), f"http://{service_name}")


def get_env_var(name: str, default=None):
    """Thin wrapper around the central ``resolve_env``."""
    return getattr(settings, name.lower(), default)


class PolicyEngineConfig:
    """Configuration class for the policy-engine service.

    The class retains the original public interface (``from_env`` and the
    attribute names) but sources all values from the cached ``settings``
    instance.
    """

    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.opa_url = OPA_URL
        self.policy_cache_ttl = POLICY_CACHE_TTL
        self.enable_redis_cache = ENABLE_REDIS_CACHE
        self.constitution_service_url = getattr(
            settings, "constitution_service_url", "http://constitution-service:10024"
        )


def get_settings():
    """Return the cached ``BaseConfig`` for the policy-engine.

    Keeping a function wrapper mirrors the original module contract, so existing
    imports (``from ...config import get_settings``) remain functional.
    """

    return settings
