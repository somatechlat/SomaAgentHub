"""
Policy-engine configuration using centralized resolver.

Two modes only: DEV and PROD. DEV mirrors PROD code paths with local fallbacks.
"""

from services.common.config.base_settings import resolve_env

SERVICE_NAME = "policy-engine"
SERVICE_PORT = int(resolve_env("SERVICE_PORT", "8083"))

# Database configuration
DATABASE_URL = resolve_env(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/soma"
)
REDIS_URL = resolve_env("POLICY_ENGINE_REDIS_URL") or resolve_env(
    "REDIS_URL", "redis://redis:6379/0"
)

# OPA configuration
OPA_URL = resolve_env("POLICY_ENGINE_OPA_URL") or resolve_env(
    "OPA_URL", "http://localhost:8181"
)

# Environment-specific configuration
ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()


# Policy configuration
def _as_bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return str(val).lower() in {"1", "true", "yes", "on"}


POLICY_CACHE_TTL = int(resolve_env("POLICY_CACHE_TTL", "300"))
ENABLE_REDIS_CACHE = _as_bool(resolve_env("ENABLE_REDIS_CACHE", "true"), True)


def get_service_url(service_name: str) -> str:
    key = f"{service_name.upper().replace('-', '_')}_URL"
    return resolve_env(key, f"http://{service_name}")


def get_env_var(name: str, default=None):
    return resolve_env(name, default)


class PolicyEngineConfig:
    """Configuration class for policy-engine service"""

    @classmethod
    def from_env(cls):
        return cls()

    def __init__(self):
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.opa_url = OPA_URL
        self.policy_cache_ttl = POLICY_CACHE_TTL
        self.enable_redis_cache = ENABLE_REDIS_CACHE
        self.constitution_service_url = resolve_env(
            "CONSTITUTION_SERVICE_URL", "http://constitution-service:10024"
        )
