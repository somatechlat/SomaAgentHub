"""Gateway service configuration primitives aligned with shared Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field

from common.config.runtime import runtime_default
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

    service_name: str = Field(
        default="sah",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_SERVICE_NAME",
            "SOMAGENT_GATEWAY_SERVICE_NAME",
            "SERVICE_NAME",
        ),
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_DEBUG",
            "SOMAGENT_GATEWAY_DEBUG",
            "DEBUG",
        ),
    )
    orchestrator_url: str = Field(
        default=runtime_default("http://orchestrator:10001", "http://orchestrator:1004"),
        validation_alias=AliasChoices(
            "SOMASTACK_SA01_URL",
            "SOMAGENT_GATEWAY_ORCHESTRATOR_URL",
            "ORCHESTRATOR_URL",
        ),
    )
    redis_url: str | None = Field(
        default=runtime_default("redis://redis:6379/0", "redis://redis.soma-infra.svc.cluster.local:6379/0"),
        validation_alias=AliasChoices(
            "SOMASTACK_REDIS_URL",
            "SOMASTACK_SAH_REDIS_URL",
            "SOMAGENT_GATEWAY_REDIS_URL",
            "REDIS_URL",
        ),
    )
    kafka_bootstrap_servers_raw: str | None = Field(
        default=runtime_default("kafka:9092", "kafka.soma-infra.svc.cluster.local:9092"),
        validation_alias=AliasChoices(
            "SOMASTACK_KAFKA_BOOTSTRAP_SERVERS",
            "SOMASTACK_SAH_KAFKA_BOOTSTRAP_SERVERS",
            "SOMAGENT_GATEWAY_KAFKA_BOOTSTRAP_SERVERS",
            "KAFKA_BOOTSTRAP_SERVERS",
        ),
    )
    auth_url_raw: str | None = Field(
        default=runtime_default("http://identity-service:10002", "http://auth.soma-infra.svc.cluster.local:8080"),
        validation_alias=AliasChoices(
            "SOMASTACK_AUTH_URL",
            "SOMASTACK_SAH_AUTH_URL",
            "SOMAGENT_GATEWAY_AUTH_URL",
            "AUTH_URL",
        ),
    )
    admin_api_url: str = Field(
        default="http://settings-service:8000",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_ADMIN_API_URL",
            "SOMAGENT_GATEWAY_ADMIN_API_URL",
            "ADMIN_API_URL",
        ),
    )
    tls_certfile: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_TLS_CERTFILE",
            "SOMAGENT_GATEWAY_TLS_CERTFILE",
            "TLS_CERTFILE",
        ),
    )
    tls_keyfile: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_TLS_KEYFILE",
            "SOMAGENT_GATEWAY_TLS_KEYFILE",
            "TLS_KEYFILE",
        ),
    )
    tls_ca_cert: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_TLS_CA_CERT",
            "SOMAGENT_GATEWAY_TLS_CA_CERT",
            "TLS_CA_CERT",
        ),
    )
    tenant_header: str = Field(
        default="X-Tenant-ID",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_TENANT_HEADER",
            "SOMAGENT_GATEWAY_TENANT_HEADER",
        ),
    )
    user_header: str = Field(
        default="X-User-ID",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_USER_HEADER",
            "SOMAGENT_GATEWAY_USER_HEADER",
        ),
    )
    capabilities_header: str = Field(
        default="X-Capabilities",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_CAPABILITIES_HEADER",
            "SOMAGENT_GATEWAY_CAPABILITIES_HEADER",
        ),
    )
    client_type_header: str = Field(
        default="X-Client-Type",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_CLIENT_TYPE_HEADER",
            "SOMAGENT_GATEWAY_CLIENT_TYPE_HEADER",
        ),
    )
    deployment_mode_header: str = Field(
        default="X-Deployment-Mode",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_DEPLOYMENT_MODE_HEADER",
            "SOMAGENT_GATEWAY_DEPLOYMENT_MODE_HEADER",
        ),
    )
    default_tenant_id: str = Field(
        default="demo",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_DEFAULT_TENANT_ID",
            "SOMAGENT_GATEWAY_DEFAULT_TENANT_ID",
        ),
    )
    default_client_type: str = Field(
        default="web",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_DEFAULT_CLIENT_TYPE",
            "SOMAGENT_GATEWAY_DEFAULT_CLIENT_TYPE",
        ),
    )
    default_deployment_mode: str = Field(
        default="developer-light",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_DEFAULT_DEPLOYMENT_MODE",
            "SOMAGENT_GATEWAY_DEFAULT_DEPLOYMENT_MODE",
        ),
    )
    jwt_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_JWT_SECRET",
            "SOMAGENT_GATEWAY_JWT_SECRET",
        ),
    )
    residency_allowed: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_RESIDENCY_ALLOWED",
            "SOMAGENT_GATEWAY_RESIDENCY_ALLOWED",
        ),
    )
    moderation_blocklist: str = Field(
        default="jailbreak, exploit, malware, self-harm",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_MODERATION_BLOCKLIST",
            "SOMAGENT_GATEWAY_MODERATION_BLOCKLIST",
        ),
    )
    moderation_strike_prefix: str = Field(
        default="moderation:strikes:",
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_MODERATION_STRIKE_PREFIX",
            "SOMAGENT_GATEWAY_MODERATION_STRIKE_PREFIX",
        ),
    )
    moderation_strike_ttl_seconds: int = Field(
        default=86_400,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_MODERATION_STRIKE_TTL_SECONDS",
            "SOMAGENT_GATEWAY_MODERATION_STRIKE_TTL_SECONDS",
        ),
    )
    moderation_block_after_strikes: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_MODERATION_BLOCK_AFTER_STRIKES",
            "SOMAGENT_GATEWAY_MODERATION_BLOCK_AFTER_STRIKES",
        ),
    )
    moderation_warning_strikes: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_MODERATION_WARNING_STRIKES",
            "SOMAGENT_GATEWAY_MODERATION_WARNING_STRIKES",
        ),
    )
    kill_switch_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SOMASTACK_SAH_KILL_SWITCH_ENABLED",
            "SOMAGENT_GATEWAY_KILL_SWITCH_ENABLED",
        ),
    )

    def resolve_jwt_secret(self) -> str:
        secret = load_secret(
            "SOMASTACK_SAH_JWT_SECRET",
            file_env="SOMASTACK_SAH_JWT_SECRET_FILE",
            default=self.jwt_secret,
        ) or load_secret(
            "SOMAGENT_GATEWAY_JWT_SECRET",
            file_env="SOMAGENT_GATEWAY_JWT_SECRET_FILE",
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
