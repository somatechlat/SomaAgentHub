"""Configuration for the notification orchestrator service."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "notification-service"
    kafka_bootstrap_servers: Optional[str] = None
    produce_topic: str = "agent.notifications"
    consume_topic: Optional[str] = None
    consumer_group: str = "notification-orchestrator"
    cache_limit: int = 500
    use_kafka: bool = True
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_NOTIFICATION_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
