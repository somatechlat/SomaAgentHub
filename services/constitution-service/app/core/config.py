"""Configuration for the constitution service."""

from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "constitution-service"
    # Service URLs are resolved via environment variables for K8s DNS.
    somabrain_base_url: str = os.getenv("SOMABRAIN_BASE_URL", "http://memory-gateway:9696")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cache_ttl_seconds: int = 30
    http_timeout_seconds: float = 30.0
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_CONSTITUTION_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
