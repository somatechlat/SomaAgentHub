"""Configuration for the Multi-Agent Orchestrator."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for MAO."""

    service_name: str = "multi-agent-orchestrator"
    debug: bool = False
    orchestrator_url: str = "http://orchestrator:8000"
    workspace_manager_url: str = "http://workspace-manager:8000"
    task_capsule_repo_url: str = "http://task-capsule-repo:8000"
    database_url: str = "postgresql+asyncpg://somagent:somagent@localhost:5432/somagent"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "mao.events"
    poll_interval_seconds: float = 1.0

    model_config = SettingsConfigDict(env_prefix="SOMAGENT_MAO_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
