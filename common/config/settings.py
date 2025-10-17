"""Centralised settings object for services running inside SomaStack.

The Settings class is the single source of truth for environment variables. It
supports both the legacy ``SOMAGENT_*`` names and the new ``SOMASTACK_*``
prefix so we can migrate services incrementally without breaking existing
deployments.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from functools import cached_property, lru_cache
from urllib.parse import urlparse

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.config.runtime import runtime_default


@dataclass(frozen=True)
class RedisConfig:
    url: str | None
    host: str | None
    port: int | None
    db: int | None


@dataclass(frozen=True)
class KafkaConfig:
    bootstrap_servers: Sequence[str]


@dataclass(frozen=True)
class AuthConfig:
    url: str | None


@dataclass(frozen=True)
class OPAConfig:
    url: str | None


@dataclass(frozen=True)
class VaultConfig:
    addr: str | None
    role: str | None
    secret_path: str | None


@dataclass(frozen=True)
class EtcdConfig:
    endpoint: str | None


@dataclass(frozen=True)
class ClickHouseConfig:
    host: str | None
    port: int | None
    database: str | None
    username: str | None
    password: str | None


class Settings(BaseSettings):
    """Primary configuration container for Soma services."""

    # Identity
    service_name: str = Field(
        default="service",
        validation_alias=AliasChoices(
            "SOMASTACK_SERVICE_NAME",
            "SOMAGENT_SERVICE_NAME",
            "SERVICE_NAME",
        ),
    )
    service_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices(
            "SOMASTACK_SERVICE_VERSION",
            "SOMAGENT_SERVICE_VERSION",
            "SERVICE_VERSION",
        ),
    )
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices(
            "SOMASTACK_ENV",
            "SOMAGENT_ENV",
            "ENVIRONMENT",
        ),
    )

    # Core infra connection strings (raw values)
    redis_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_REDIS_URL",
            "SOMAGENT_REDIS_URL",
            "REDIS_URL",
        ),
    )
    kafka_bootstrap_servers_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_KAFKA_BOOTSTRAP_SERVERS",
            "SOMAGENT_KAFKA_BOOTSTRAP_SERVERS",
            "KAFKA_BOOTSTRAP_SERVERS",
        ),
    )
    auth_url_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_AUTH_URL",
            "SOMAGENT_AUTH_URL",
            "AUTH_URL",
        ),
    )
    opa_url_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_OPA_URL",
            "SOMAGENT_OPA_URL",
            "OPA_URL",
        ),
    )
    vault_addr_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_VAULT_ADDR",
            "SOMAGENT_VAULT_ADDR",
            "VAULT_ADDR",
        ),
    )
    vault_role: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_VAULT_ROLE",
            "SOMAGENT_VAULT_ROLE",
            "VAULT_ROLE",
        ),
    )
    vault_secret_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_VAULT_SECRET_PATH",
            "SOMAGENT_VAULT_SECRET_PATH",
            "VAULT_SECRET_PATH",
        ),
    )
    etcd_endpoint_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_ETCD_ENDPOINT",
            "SOMAGENT_ETCD_ENDPOINT",
            "ETCD_ENDPOINT",
        ),
    )
    clickhouse_host_raw: str | None = Field(
        default=runtime_default("clickhouse", "clickhouse.soma-infra.svc.cluster.local"),
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_HOST",
            "SOMAGENT_CLICKHOUSE_HOST",
            "CLICKHOUSE_HOST",
        ),
    )
    clickhouse_port_raw: str | None = Field(
        default="9000",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_PORT",
            "SOMAGENT_CLICKHOUSE_PORT",
            "CLICKHOUSE_PORT",
        ),
    )
    clickhouse_database: str | None = Field(
        default="somastack_audit",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_DATABASE",
            "SOMAGENT_CLICKHOUSE_DATABASE",
            "CLICKHOUSE_DATABASE",
        ),
    )
    clickhouse_username: str | None = Field(
        default="default",
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_USERNAME",
            "SOMAGENT_CLICKHOUSE_USERNAME",
            "CLICKHOUSE_USERNAME",
        ),
    )
    clickhouse_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_CLICKHOUSE_PASSWORD",
            "SOMAGENT_CLICKHOUSE_PASSWORD",
            "CLICKHOUSE_PASSWORD",
        ),
    )

    # Observability
    enable_otlp: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SOMASTACK_ENABLE_OTLP",
            "SOMAGENT_ENABLE_OTLP",
            "ENABLE_OTLP",
        ),
    )
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SOMASTACK_OTEL_EXPORTER_OTLP_ENDPOINT",
            "SOMAGENT_OTEL_EXPORTER_OTLP_ENDPOINT",
            "OTEL_EXPORTER_OTLP_ENDPOINT",
        ),
    )

    model_config = SettingsConfigDict(env_prefix="SOMASTACK_", extra="allow")

    @cached_property
    def redis(self) -> RedisConfig:
        url = self.redis_url
        if not url:
            return RedisConfig(url=None, host=None, port=None, db=None)

        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        db = None
        if parsed.path:
            with suppress(ValueError):
                db = int(parsed.path.lstrip("/"))
        return RedisConfig(url=url, host=host, port=port, db=db)

    @cached_property
    def kafka(self) -> KafkaConfig:
        raw = self.kafka_bootstrap_servers_raw
        if not raw:
            return KafkaConfig(bootstrap_servers=[])
        servers = [item.strip() for item in raw.split(",") if item.strip()]
        return KafkaConfig(bootstrap_servers=servers)

    @cached_property
    def auth(self) -> AuthConfig:
        return AuthConfig(url=self.auth_url_raw)

    @cached_property
    def opa(self) -> OPAConfig:
        return OPAConfig(url=self.opa_url_raw)

    @cached_property
    def vault(self) -> VaultConfig:
        return VaultConfig(
            addr=self.vault_addr_raw,
            role=self.vault_role,
            secret_path=self.vault_secret_path,
        )

    @cached_property
    def etcd(self) -> EtcdConfig:
        return EtcdConfig(endpoint=self.etcd_endpoint_raw)

    @cached_property
    def clickhouse(self) -> ClickHouseConfig:
        port_value: int | None = None
        if self.clickhouse_port_raw:
            with suppress(ValueError):
                port_value = int(self.clickhouse_port_raw)
        return ClickHouseConfig(
            host=self.clickhouse_host_raw,
            port=port_value,
            database=self.clickhouse_database,
            username=self.clickhouse_username,
            password=self.clickhouse_password,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Backwards compatibility exports
CommonSettings = Settings  # type: ignore


@lru_cache
def get_common_settings() -> Settings:
    return get_settings()
