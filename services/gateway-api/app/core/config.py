"""Placeholder config for gateway API.

Provides minimal settings required for import.
"""

from __future__ import annotations

from functools import lru_cache

SERVICE_NAME = "gateway-api"
SERVICE_PORT = 8080

class GatewaySettings:
    def __init__(self) -> None:
        self.service_name = SERVICE_NAME
        self.service_port = SERVICE_PORT

        @lru_cache
    def get_settings() -> GatewaySettings:
        return GatewaySettings()

        settings = get_settings()"""Placeholder config for gateway API.

        Provides minimal settings required for import.
        """

        from __future__ import annotations

        from functools import lru_cache

        SERVICE_NAME = "gateway-api"
        SERVICE_PORT = 8080

        class GatewaySettings:
    def __init__(self) -> None:
        self.service_name = SERVICE_NAME
        self.service_port = SERVICE_PORT

        @lru_cache
    def get_settings() -> GatewaySettings:
    return GatewaySettings()

    settings = get_settings()"""Gateway service configuration using centralized resolver and Vault client."""

    from __future__ import annotations

    from functools import lru_cache

    from services.common.config.base_settings import resolve_env
    from services.common.vault_client import init_vault

# Service-specific configuration
    SERVICE_NAME = "gateway-api"
    SERVICE_PORT = int(resolve_env("SERVICE_PORT", "8080"))

# Database configuration
    DATABASE_URL = resolve_env(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/soma"
    )
    REDIS_URL = resolve_env("GATEWAY_REDIS_URL") or resolve_env(
    "REDIS_URL", "redis://redis:6379/0"
    )


# Service dependencies (using registry for discovery)
    def _svc(name: str, default: str) -> str:
# Prefer service-specific vars, then generic, then default
        return (
        resolve_env(f"GATEWAY_{name.upper()}_URL")
        or resolve_env(f"{name.upper()}_URL")
        or default
        )


        ORCHESTRATOR_URL = _svc("orchestrator", "http://orchestrator:8000")
        PRICING_SERVICE_URL = _svc("pricing-service", "http://pricing-service:10026")
        AUTH_URL = _svc("identity-service", "http://identity-service:10030")
        ADMIN_API_URL = _svc("settings-service", "http://settings-service:10032")


# Security configuration
    def _get_jwt_secret() -> str:
            env_secret = resolve_env("JWT_SECRET")
            if env_secret:
                return env_secret
                try:
                    client = init_vault(role=SERVICE_NAME)
                    secret = client.read_secret("jwt").data.get("secret")
                    if secret:
                        return secret
                        except Exception as exc:  # pragma: no cover
 # Log the exception for debugging purposes; fallback to default secret
 import logging

 logging.getLogger(__name__).exception("Failed to retrieve JWT secret from Vault")
 # Continue to return the default dev secret below
 return resolve_env("JWT_SECRET", "dev-jwt-secret")


 JWT_SECRET = _get_jwt_secret()

# Feature flags
 DEBUG = (resolve_env("DEBUG", "false") or "false").lower() == "true"
 KILL_SWITCH_ENABLED = (
 resolve_env("KILL_SWITCH_ENABLED", "false") or "false"
 ).lower() == "true"

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
 TLS_CERTFILE = resolve_env("TLS_CERTFILE")
 TLS_KEYFILE = resolve_env("TLS_KEYFILE")
 TLS_CA_CERT = resolve_env("TLS_CA_CERT")


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
# Placeholder objects for compatibility with existing code expecting
# ``settings.kafka.bootstrap_servers`` and ``settings.auth.url``.
         self.kafka = type("KafkaConfig", (), {"bootstrap_servers": []})()
         self.auth = type("AuthConfig", (), {"url": None})()
# Service version for FastAPI metadata and observability
         self.service_version = "0.1.0"
# Service version for FastAPI metadata and observability
         self.service_version = "0.1.0"

    def moderation_terms(self) -> list[str]:
        return [
        term.strip().lower()
        for term in MODERATION_BLOCKLIST.split(",")
        if term.strip()
        ]


        @lru_cache
    def get_settings() -> GatewaySettings:
        """Return cached settings instance."""
        return GatewaySettings()


        settings = get_settings()
