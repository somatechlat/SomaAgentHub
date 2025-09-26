"""Configuration for tool integration service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings."""

    service_name: str = "tool-service"
    debug: bool = False
    registry_path: str = "./data/tool-registry.json"
    sandbox_base_path: str = "/tmp/somagent/sandbox"
    release_signing_secret: str = "development-secret"
    default_rate_limit_per_minute: int = 30
    analytics_url: str | None = "http://analytics-service:8000"
    billing_default_currency: str = "USD"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_TOOL_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
