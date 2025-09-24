"""Configuration for notification orchestrator."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "notification-orchestrator"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "notifications.events"
    websocket_prefix: str = "/ws/notifications"
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_NOTIFY_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
