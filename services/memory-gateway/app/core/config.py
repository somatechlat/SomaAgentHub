"""Configuration for memory gateway."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "memory-gateway"
    somabrain_url: str = "http://localhost:9696"
    tenant_header: str = "X-Tenant-ID"
    default_tenant_id: str = "demo"
    http_timeout_seconds: float = 30.0
    redis_url: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_MEMORY_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
