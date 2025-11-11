"""Gateway service configuration wrapper to core settings."""

from services.gateway-api.app.core.config import (
    GatewaySettings,
    get_settings,
    SERVICE_NAME,
    SERVICE_PORT,
    DATABASE_URL,
    REDIS_URL,
    ORCHESTRATOR_URL,
    PRICING_SERVICE_URL,
    JWT_SECRET,
)

# Environment mode helpers via centralized resolver
try:
    from services.common.config.base_settings import resolve_env
except Exception:
    import os
    def resolve_env(name: str, default: str | None = None):
        return os.getenv(f"SOMA_AGENT_HUB_{name}") or os.getenv(f"SOMAGENT_{name}") or os.getenv(f"SOMASTACK_{name}") or os.getenv(name, default)

ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()

def get_service_url(service_name: str):
    # Best-effort mapping via env
    return (
        resolve_env(f"{service_name.upper().replace('-', '_')}_URL")
        or ""
    )
