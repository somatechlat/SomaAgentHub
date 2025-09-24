"""Orchestrator configuration primitives."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the orchestrator."""

    service_name: str = "orchestrator"
    debug: bool = False
    constitution_service_url: str = "http://constitution-service:8000"
    policy_engine_url: str = "http://policy-engine:8000"
    slm_service_url: str = "http://slm-service:8000"
    memory_gateway_url: str = "http://memory-gateway:8000"

    model_config = SettingsConfigDict(env_prefix="SOMAGENT_ORCHESTRATOR_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
