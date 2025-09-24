"""Configuration for task capsule repository."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    service_name: str = "task-capsule-repo"
    postgres_url: str = "postgresql+asyncpg://somagent:somagent@postgres:5432/capsules"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_CAPSULES_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
