"""Configuration for the constitution service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "constitution-service"
    somabrain_base_url: str = "http://localhost:9696"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 30
    http_timeout_seconds: float = 30.0
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_CONSTITUTION_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
