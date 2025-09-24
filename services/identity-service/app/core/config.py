"""Configuration for identity service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "identity-service"
    debug: bool = False
    jwk_set_url: str = "https://auth.example.com/.well-known/jwks.json"
    redis_url: str = "redis://redis:6379/0"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_IDENTITY_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
