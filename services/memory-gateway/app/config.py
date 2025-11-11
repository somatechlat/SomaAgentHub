"""
Unified Configuration for memory-gateway service
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
deployment_config = get_deployment_config("memory-gateway")

# Service-specific configuration
SERVICE_NAME = "memory-gateway"
SERVICE_PORT = settings.service_ports.get("memory_gateway", 8082)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# Vector store configuration
QDRANT_URL = os.getenv("SOMASTACK_QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("SOMASTACK_QDRANT_API_KEY", "")

# Object storage configuration
OBJECT_STORE_BUCKET = settings.object_store_bucket
OBJECT_STORE_REGION = settings.object_store_region

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
def get_env_var(name: str, default=None):
    """Get environment variable with fallback to settings"""
    return os.getenv(name, getattr(settings, name.lower(), default))

# Configuration class for backward compatibility
class MemoryGatewayConfig:
    """Configuration class for memory-gateway service"""
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment"""
        return cls()
    
    def __init__(self):
        self.qdrant_url = QDRANT_URL
        self.qdrant_api_key = QDRANT_API_KEY
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.bucket_name = OBJECT_STORE_BUCKET
        self.region = OBJECT_STORE_REGION