"""Gateway service configuration primitives."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from somagent_secrets import load_secret


class Settings(BaseSettings):
    """Runtime configuration for the Gateway API service."""

    service_name: str = "gateway-api"
    debug: bool = False
    orchestrator_url: str = "http://orchestrator:8000"
    admin_api_url: str = "http://settings-service:8000"
    redis_url: str = "redis://redis:6379/0"
    tls_certfile: str | None = None
    tls_keyfile: str | None = None
    tls_ca_cert: str | None = None
    tenant_header: str = "X-Tenant-ID"
    user_header: str = "X-User-ID"
    capabilities_header: str = "X-Capabilities"
    client_type_header: str = "X-Client-Type"
    deployment_mode_header: str = "X-Deployment-Mode"
    default_tenant_id: str = "demo"
    default_client_type: str = "web"
    default_deployment_mode: str = "developer-light"
    jwt_secret: str | None = None
    residency_allowed: str = ""
    moderation_blocklist: str = "jailbreak, exploit, malware, self-harm"
    moderation_strike_prefix: str = "moderation:strikes:"
    moderation_strike_ttl_seconds: int = 86_400
    moderation_block_after_strikes: int = 1
    moderation_warning_strikes: int = 1
    kill_switch_enabled: bool = False

    model_config = SettingsConfigDict(env_prefix="SOMAGENT_GATEWAY_", extra="allow")

    def resolve_jwt_secret(self) -> str:
        secret = load_secret("SOMAGENT_GATEWAY_JWT_SECRET", file_env="SOMAGENT_GATEWAY_JWT_SECRET_FILE", default=self.jwt_secret)
        if not secret:
            raise ValueError("Gateway JWT secret not configured")
        return secret

    def moderation_terms(self) -> list[str]:
        terms = []
        for raw in self.moderation_blocklist.split(","):
            term = raw.strip().lower()
            if term:
                terms.append(term)
        return terms

    def allowed_tenants(self) -> list[str]:
        if not self.residency_allowed:
            return []
        tenants: list[str] = []
        for raw in self.residency_allowed.split(","):
            tenant = raw.strip()
            if tenant:
                tenants.append(tenant)
        return tenants


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated environment parsing."""

    return Settings()


settings = get_settings()
