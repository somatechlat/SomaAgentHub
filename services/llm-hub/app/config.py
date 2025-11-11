"""
Unified Configuration for llm-hub service
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
deployment_config = get_deployment_config("llm-hub")

# Service-specific configuration
SERVICE_NAME = "llm-hub"
SERVICE_PORT = settings.service_ports.get("llm_hub", 8084)

# Database configuration
DATABASE_URL = deployment_config.database_url

# API Keys (loaded from Vault in production)
OPENAI_API_KEY = vault.get_secret("services/llm-hub", "openai_api_key") or os.getenv("SOMASTACK_OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = vault.get_secret("services/llm-hub", "anthropic_api_key") or os.getenv("SOMASTACK_ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = vault.get_secret("services/llm-hub", "google_api_key") or os.getenv("SOMASTACK_GOOGLE_API_KEY", "")

# Model configuration
DEFAULT_MODEL_PROVIDER = os.getenv("SOMASTACK_DEFAULT_MODEL_PROVIDER", settings.default_model_provider)
DEFAULT_MODEL = os.getenv("SOMASTACK_DEFAULT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("SOMASTACK_MAX_TOKENS", "4000"))
TEMPERATURE = float(os.getenv("SOMASTACK_TEMPERATURE", "0.7"))

# Rate limiting
REQUESTS_PER_MINUTE = int(os.getenv("SOMASTACK_REQUESTS_PER_MINUTE", "60"))
TOKENS_PER_MINUTE = int(os.getenv("SOMASTACK_TOKENS_PER_MINUTE", "40000"))

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
class LLMHubConfig:
    """Configuration class for llm-hub service"""
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment"""
        return cls()
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.openai_api_key = OPENAI_API_KEY
        self.anthropic_api_key = ANTHROPIC_API_KEY
        self.google_api_key = GOOGLE_API_KEY
        self.default_model_provider = DEFAULT_MODEL_PROVIDER
        self.default_model = DEFAULT_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self.requests_per_minute = REQUESTS_PER_MINUTE
        self.tokens_per_minute = TOKENS_PER_MINUTE