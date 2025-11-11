"""
Unified Configuration for policy-engine service
Migrated to use centralized settings
"""

import os
from services.common.config.unified_settings import get_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager
from services.common.deployment.deployment_strategy import get_deployment_config

# Get unified settings
settings = get_settings()
registry = get_service_registry()
vault = get_vault_manager()
deployment_config = get_deployment_config("policy-engine")

# Service-specific configuration
SERVICE_NAME = "policy-engine"
SERVICE_PORT = settings.service_ports.get("policy_engine", 8083)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# OPA configuration
OPA_URL = os.getenv("SOMASTACK_OPA_URL", "http://localhost:8181")

# Service discovery
SERVICE_REGISTRY = registry

# Secrets management
SECRETS = vault.get_service_secrets(SERVICE_NAME)

# Environment-specific configuration
ENVIRONMENT = settings.environment
DEPLOYMENT_MODE = settings.deployment_mode

# Policy configuration
POLICY_CACHE_TTL = int(os.getenv("SOMASTACK_POLICY_CACHE_TTL", "300"))
ENABLE_REDIS_CACHE = os.getenv("SOMASTACK_ENABLE_REDIS_CACHE", "true").lower() == "true"

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
def get_env_var(name: str, default=None):
    """Get environment variable with fallback to settings"""
    return os.getenv(name, getattr(settings, name.lower(), default))

# Configuration class for backward compatibility
class PolicyEngineConfig:
    """Configuration class for policy-engine service"""
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment"""
        return cls()
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.opa_url = OPA_URL
        self.policy_cache_ttl = POLICY_CACHE_TTL
        self.enable_redis_cache = ENABLE_REDIS_CACHE
        self.constitution_service_url = os.getenv("SOMASTACK_CONSTITUTION_SERVICE_URL", "http://localhost:10024")