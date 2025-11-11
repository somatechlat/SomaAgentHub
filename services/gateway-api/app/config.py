"""Gateway service configuration helpers using unified settings."""

from services.common.config.unified_settings import get_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager
from services.common.deployment.deployment_strategy import get_deployment_config

# Get unified settings
settings = get_settings()
registry = get_service_registry()
vault = get_vault_manager()
deployment_config = get_deployment_config("gateway-api")

# Service-specific configuration
SERVICE_NAME = "gateway-api"
SERVICE_PORT = settings.service_ports.get("gateway_api", 8080)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# Service dependencies
ORCHESTRATOR_URL = registry.get_service_url("orchestrator") if "orchestrator" in registry.services else "http://localhost:8081"
PRICING_SERVICE_URL = registry.get_service_url("pricing-service") if "pricing-service" in registry.services else "http://localhost:8085"

# Security configuration
JWT_SECRET = vault.get_secret("jwt", "secret") or settings.jwt_secret

# Service discovery
SERVICE_REGISTRY = registry

# Secrets management
SECRETS = vault.get_service_secrets(SERVICE_NAME)

# Environment-specific configuration
ENVIRONMENT = settings.environment
DEPLOYMENT_MODE = settings.deployment_mode

# Quick access functions
def get_service_url(service_name: str):
    """Get URL for another service"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(registry.get_service_url(service_name))
    finally:
        loop.close()

# Legacy compatibility
GatewaySettings = deployment_config
get_sah_settings = lambda: deployment_config
