"""Gateway service configuration primitives aligned with shared Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from common.config.settings import Settings as SharedSettings


def load_secret(env_var: str, file_env: str | None = None, default: str | None = None) -> str:
    """Load a secret from environment variable or mounted file."""

    import os

    value = os.getenv(env_var)
    if value:
        return value
    if file_env:
        file_path = os.getenv(file_env)
        if file_path:
            path = Path(file_path)
            if path.is_file():
                try:
                    return path.read_text(encoding="utf-8").strip()
                except Exception:  # pragma: no cover - best effort fallback
                    pass
    return default or ""


class GatewaySettings(SharedSettings):
    """Settings object for SomaAgentHub (SAH) service."""

    service_name: str = Field(default="sah", alias="SERVICE_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    orchestrator_url: str = Field(default="http://orchestrator:10001", alias="ORCHESTRATOR_URL")
    redis_url: str | None = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    kafka_bootstrap_servers_raw: str | None = Field(default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    auth_url_raw: str | None = Field(default="http://identity-service:10002", alias="AUTH_URL")
    admin_api_url: str = Field(default="http://settings-service:8000", alias="ADMIN_API_URL")
    tls_certfile: str | None = Field(default=None, alias="TLS_CERTFILE")
    tls_keyfile: str | None = Field(default=None, alias="TLS_KEYFILE")
    tls_ca_cert: str | None = Field(default=None, alias="TLS_CA_CERT")
    tenant_header: str = Field(default="X-Tenant-ID")
    user_header: str = Field(default="X-User-ID")
    capabilities_header: str = Field(default="X-Capabilities")
    client_type_header: str = Field(default="X-Client-Type")
    deployment_mode_header: str = Field(default="X-Deployment-Mode")
    default_tenant_id: str = Field(default="demo")
    default_client_type: str = Field(default="web")
    default_deployment_mode: str = Field(default="developer-light")
    jwt_secret: str | None = Field(default=None, alias="SOMAGENT_IDENTITY_JWT_SECRET")
    residency_allowed: str = Field(default="")
    moderation_blocklist: str = Field(default="jailbreak, exploit, malware, self-harm")
    moderation_strike_prefix: str = Field(default="moderation:strikes:")
    moderation_strike_ttl_seconds: int = Field(default=86_400)
    moderation_block_after_strikes: int = Field(default=1)
    moderation_warning_strikes: int = Field(default=1)
    kill_switch_enabled: bool = Field(default=False)

    def resolve_jwt_secret(self) -> str:
        secret = load_secret(
            "SOMAGENT_IDENTITY_JWT_SECRET",
            file_env="SOMAGENT_IDENTITY_JWT_SECRET_FILE",
            default=self.jwt_secret,
        )
        if not secret:
            raise ValueError("Gateway JWT secret not configured")
        return secret

    def moderation_terms(self) -> list[str]:
        return [term.strip().lower() for term in self.moderation_blocklist.split(",") if term.strip()]

    def allowed_tenants(self) -> list[str]:
        if not self.residency_allowed:
            return []
        return [tenant.strip() for tenant in self.residency_allowed.split(",") if tenant.strip()]


@lru_cache
def get_settings() -> GatewaySettings:
    """Return cached settings instance to avoid repeated environment parsing."""

    return GatewaySettings()


settings = get_settings()
