"""Gateway service configuration primitives using unified settings."""

from __future__ import annotations

from functools import lru_cache
import os
from services.common.config.unified_settings import get_settings as get_unified_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager
from services.common.deployment.deployment_strategy import get_deployment_config

# Get unified settings
settings = get_unified_settings()
registry = get_service_registry()
vault = get_vault_manager()
deployment_config = get_deployment_config("gateway-api")

# Service-specific configuration
SERVICE_NAME = "gateway-api"
SERVICE_PORT = settings.service_ports.get("gateway_api", 8080)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# Service dependencies (using registry for discovery)
def get_service_url(service_name: str, default_path: str = "") -> str:
    """Get service URL with fallback to defaults"""
    try:
        return registry.get_service_url(service_name)
    except:
        port = settings.service_ports.get(service_name, 8080)
        return f"http://localhost:{port}{default_path}"

ORCHESTRATOR_URL = get_service_url("orchestrator")
PRICING_SERVICE_URL = get_service_url("pricing-service")
AUTH_URL = get_service_url("identity-service")
ADMIN_API_URL = get_service_url("settings-service")

# Security configuration
JWT_SECRET = vault.get_secret("jwt", "secret") or settings.jwt_secret

# Feature flags
DEBUG = os.getenv("SOMASTACK_DEBUG", "false").lower() == "true"
KILL_SWITCH_ENABLED = os.getenv("SOMASTACK_KILL_SWITCH_ENABLED", "false").lower() == "true"

# Headers and defaults
TENANT_HEADER = "X-Tenant-ID"
USER_HEADER = "X-User-ID"
CAPABILITIES_HEADER = "X-Capabilities"
CLIENT_TYPE_HEADER = "X-Client-Type"
DEPLOYMENT_MODE_HEADER = "X-Deployment-Mode"
DEFAULT_TENANT_ID = "demo"
DEFAULT_CLIENT_TYPE = "web"
DEFAULT_DEPLOYMENT_MODE = "developer-light"

# Moderation settings
MODERATION_BLOCKLIST = "jailbreak, exploit, malware, self-harm"
MODERATION_STRIKE_PREFIX = "moderation:strikes:"
MODERATION_STRIKE_TTL_SECONDS = 86400
MODERATION_BLOCK_AFTER_STRIKES = 1
MODERATION_WARNING_STRIKES = 1

# TLS configuration
TLS_CERTFILE = os.getenv("SOMASTACK_TLS_CERTFILE")
TLS_KEYFILE = os.getenv("SOMASTACK_TLS_KEYFILE")
TLS_CA_CERT = os.getenv("SOMASTACK_TLS_CA_CERT")

class GatewaySettings:
    """Unified configuration settings for gateway service"""
    
    def __init__(self):
        self.service_name = SERVICE_NAME
        self.debug = DEBUG
        self.orchestrator_url = ORCHESTRATOR_URL
        self.pricing_service_url = PRICING_SERVICE_URL
        self.redis_url = REDIS_URL
        self.auth_url = AUTH_URL
        self.admin_api_url = ADMIN_API_URL
        self.tls_certfile = TLS_CERTFILE
        self.tls_keyfile = TLS_KEYFILE
        self.tls_ca_cert = TLS_CA_CERT
        self.tenant_header = TENANT_HEADER
        self.user_header = USER_HEADER
        self.capabilities_header = CAPABILITIES_HEADER
        self.client_type_header = CLIENT_TYPE_HEADER
        self.deployment_mode_header = DEPLOYMENT_MODE_HEADER
        self.default_tenant_id = DEFAULT_TENANT_ID
        self.default_client_type = DEFAULT_CLIENT_TYPE
        self.default_deployment_mode = DEFAULT_DEPLOYMENT_MODE
        self.jwt_secret = JWT_SECRET
        self.kill_switch_enabled = KILL_SWITCH_ENABLED
    
    def moderation_terms(self) -> list[str]:
        return [term.strip().lower() for term in MODERATION_BLOCKLIST.split(",") if term.strip()]

@lru_cache
def get_settings() -> GatewaySettings:
    """Return cached settings instance."""
    return GatewaySettings()

settings = get_settings()
