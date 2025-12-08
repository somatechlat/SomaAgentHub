"""Configuration for identity service aligned with shared SomaStack settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field

from services.common.config.base_config import BaseConfig as SharedSettings
from services.common.config.base_settings import resolve_env
from services.common.config.runtime import runtime_default


def load_secret(
    env_var: str, file_env: str | None = None, default: str | None = None
) -> str:
    """Load a secret from environment variable or mounted file."""

    value = resolve_env(env_var)
    if value:
        return value
    if file_env:
        file_path = resolve_env(file_env)
        if file_path:
            path = Path(file_path)
            if path.is_file():
                try:
                    return path.read_text(encoding="utf-8").strip()
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Failed to read secret from file {path}: {e}"
                    )
    return default or ""


class IdentitySettings(SharedSettings):
    """Runtime configuration surfaced via the shared settings layer."""

    # Updated to use the canonical ``SOMA_AGENT_HUB_`` prefix only.
    service_name: str = Field(
        default="identity-service",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_SERVICE_NAME",
            "SERVICE_NAME",
        ),
    )
    service_version: str = Field(
        default="0.2.0",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_SERVICE_VERSION",
            "SERVICE_VERSION",
        ),
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_DEBUG",
            "DEBUG",
        ),
    )
    jwk_set_url: str = Field(
        default=runtime_default(
            resolve_env(
                "IDENTITY_JWKS_URL",
                "http://identity-service:10002/.well-known/jwks.json",
            ),
            "https://auth.soma-infra.svc.cluster.local:8080/.well-known/jwks.json",
        ),
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_JWK_SET_URL",
            "JWK_SET_URL",
        ),
    )
    redis_url: str | None = Field(
        default=runtime_default(
            resolve_env("REDIS_URL", "redis://redis:6379/0"),
            "redis://redis.soma-infra.svc.cluster.local:6379/0",
        ),
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_REDIS_URL",
            "REDIS_URL",
        ),
    )
    key_rotation_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_KEY_ROTATION_SECONDS",
            "KEY_ROTATION_SECONDS",
        ),
    )
    key_rotation_check_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_KEY_ROTATION_CHECK_SECONDS",
            "KEY_ROTATION_CHECK_SECONDS",
        ),
    )
    key_namespace: str = Field(
        default="identity:keys",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_IDENTITY_KEY_NAMESPACE",
            "KEY_NAMESPACE",
        ),
    )
    clickhouse_host_raw: str | None = Field(
        default=runtime_default(
            "clickhouse", "clickhouse.soma-infra.svc.cluster.local"
        ),
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_CLICKHOUSE_HOST",
            "CLICKHOUSE_HOST",
        ),
    )
    clickhouse_port_raw: str | None = Field(
        default="9000",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_CLICKHOUSE_PORT",
            "CLICKHOUSE_PORT",
        ),
    )
    clickhouse_database: str | None = Field(
        default="somastack_audit",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_CLICKHOUSE_DATABASE",
            "CLICKHOUSE_DATABASE",
        ),
    )
    clickhouse_username: str | None = Field(
        default="default",
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_CLICKHOUSE_USERNAME",
            "CLICKHOUSE_USERNAME",
        ),
    )
    clickhouse_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMA_AGENT_HUB_CLICKHOUSE_PASSWORD",
            "CLICKHOUSE_PASSWORD",
        ),
    )

    @property
    def clickhouse(self):
        from dataclasses import dataclass

        @dataclass
        class ClickHouseConfig:
            host: str | None
            port: int | None
            database: str | None
            username: str | None
            password: str | None

        return ClickHouseConfig(
            host=self.clickhouse_host_raw,
            port=int(self.clickhouse_port_raw) if self.clickhouse_port_raw else None,
            database=self.clickhouse_database,
            username=self.clickhouse_username,
            password=self.clickhouse_password,
        )

    # JWT symmetric secrets deprecated; Identity uses RS256 with live JWKS.


@lru_cache
def get_settings() -> IdentitySettings:
    """Return cached settings."""

    return IdentitySettings()


settings = get_settings()
