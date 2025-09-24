"""Configuration for the policy engine."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings."""

    service_name: str = "policy-engine"
    debug: bool = False
    default_threshold: float = 0.7
    production_threshold: float = 0.8
    risk_weight: float = 0.4
    confidence_weight: float = 0.4
    cost_weight: float = 0.2
    human_gate_penalty: float = 0.15
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_POLICY_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()


settings = get_settings()
