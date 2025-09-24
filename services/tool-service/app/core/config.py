"""Configuration for tool integration service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings."""

    service_name: str = "tool-service"
    debug: bool = False
    registry_path: str = "./data/tool-registry.json"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_TOOL_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
