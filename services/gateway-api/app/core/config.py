"""Gateway service configuration primitives."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Gateway API service."""

    service_name: str = "gateway-api"
    debug: bool = False
    orchestrator_url: str = "http://orchestrator:8000"
    admin_api_url: str = "http://settings-service:8000"
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

    model_config = SettingsConfigDict(env_prefix="SOMAGENT_GATEWAY_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated environment parsing."""

    return Settings()


settings = get_settings()
