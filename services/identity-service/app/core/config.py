"""Configuration for identity service aligned with shared SomaStack settings."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field

from common.config.settings import Settings as SharedSettings


def load_secret(env_var: str, file_env: str | None = None, default: str | None = None) -> str:
    """Load a secret from environment variable or mounted file."""

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


class IdentitySettings(SharedSettings):
    """Runtime configuration surfaced via the shared settings layer."""

    service_name: str = Field(
        default="identity-service",
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_SERVICE_NAME",
            "SOMAGENT_IDENTITY_SERVICE_NAME",
            "SERVICE_NAME",
        ),
    )
    service_version: str = Field(
        default="0.2.0",
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_SERVICE_VERSION",
            "SOMAGENT_IDENTITY_SERVICE_VERSION",
            "SERVICE_VERSION",
        ),
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_DEBUG",
            "SOMAGENT_IDENTITY_DEBUG",
            "DEBUG",
        ),
    )
    jwk_set_url: str = Field(
        default="https://auth.soma-infra.svc.cluster.local:8080/.well-known/jwks.json",
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_JWK_SET_URL",
            "SOMAGENT_IDENTITY_JWK_SET_URL",
            "JWK_SET_URL",
        ),
    )
    redis_url: str | None = Field(
        default="redis://redis.soma-infra.svc.cluster.local:6379/0",
        validation_alias=AliasChoices(
            "SOMASTACK_REDIS_URL",
            "SOMASTACK_IDENTITY_REDIS_URL",
            "SOMAGENT_IDENTITY_REDIS_URL",
            "REDIS_URL",
        ),
    )
    jwt_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_JWT_SECRET",
            "SOMAGENT_IDENTITY_JWT_SECRET",
        ),
    )
    key_rotation_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_KEY_ROTATION_SECONDS",
            "SOMAGENT_IDENTITY_KEY_ROTATION_SECONDS",
            "KEY_ROTATION_SECONDS",
        ),
    )
    key_rotation_check_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_KEY_ROTATION_CHECK_SECONDS",
            "SOMAGENT_IDENTITY_KEY_ROTATION_CHECK_SECONDS",
            "KEY_ROTATION_CHECK_SECONDS",
        ),
    )
    key_namespace: str = Field(
        default="identity:keys",
        validation_alias=AliasChoices(
            "SOMASTACK_IDENTITY_KEY_NAMESPACE",
            "SOMAGENT_IDENTITY_KEY_NAMESPACE",
            "KEY_NAMESPACE",
        ),
    )
    clickhouse_host_raw: str | None = Field(
        default="clickhouse.soma-infra.svc.cluster.local",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_HOST",
            "SOMASTACK_IDENTITY_CLICKHOUSE_HOST",
            "SOMAGENT_IDENTITY_CLICKHOUSE_HOST",
            "CLICKHOUSE_HOST",
        ),
    )
    clickhouse_port_raw: str | None = Field(
        default="9000",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_PORT",
            "SOMASTACK_IDENTITY_CLICKHOUSE_PORT",
            "SOMAGENT_IDENTITY_CLICKHOUSE_PORT",
            "CLICKHOUSE_PORT",
        ),
    )
    clickhouse_database: str | None = Field(
        default="somastack_audit",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_DATABASE",
            "SOMASTACK_IDENTITY_CLICKHOUSE_DATABASE",
            "SOMAGENT_IDENTITY_CLICKHOUSE_DATABASE",
            "CLICKHOUSE_DATABASE",
        ),
    )
    clickhouse_username: str | None = Field(
        default="default",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_USERNAME",
            "SOMASTACK_IDENTITY_CLICKHOUSE_USERNAME",
            "SOMAGENT_IDENTITY_CLICKHOUSE_USERNAME",
            "CLICKHOUSE_USERNAME",
        ),
    )
    clickhouse_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_PASSWORD",
            "SOMASTACK_IDENTITY_CLICKHOUSE_PASSWORD",
            "SOMAGENT_IDENTITY_CLICKHOUSE_PASSWORD",
            "CLICKHOUSE_PASSWORD",
        ),
    )

    def resolve_jwt_secret(self) -> str:
        secret = load_secret(
            "SOMASTACK_IDENTITY_JWT_SECRET",
            file_env="SOMASTACK_IDENTITY_JWT_SECRET_FILE",
            default=self.jwt_secret,
        ) or load_secret(
            "SOMAGENT_IDENTITY_JWT_SECRET",
            file_env="SOMAGENT_IDENTITY_JWT_SECRET_FILE",
            default=self.jwt_secret,
        )
        if not secret:
            raise ValueError("Identity JWT secret not configured")
        return secret

@lru_cache
def get_settings() -> IdentitySettings:
    """Return cached settings."""

    return IdentitySettings()


settings = get_settings()
