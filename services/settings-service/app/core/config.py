"""Configuration for settings service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for configuration service."""

    service_name: str = "settings-service"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://somagent:somagent@postgres:5432/settings"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_SETTINGS_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
