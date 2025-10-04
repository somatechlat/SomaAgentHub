"""Configuration primitives for the orchestrator service.

This module centralises environment-driven configuration so both the FastAPI
application and Temporal workers consume the same values.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from the environment."""

    service_name: str = Field(default="orchestrator-service")

    # Temporal configuration
    temporal_target_host: str = Field(default="temporal:7233", alias="TEMPORAL_TARGET_HOST")
    temporal_namespace: str = Field(default="default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field(default="somagent.session.workflows", alias="TEMPORAL_TASK_QUEUE")

    # Kafka audit stream
    kafka_bootstrap_servers: Optional[str] = Field(default=None, alias="KAFKA_BOOTSTRAP_SERVERS")

    # Policy & identity services (real HTTP endpoints)
    policy_engine_url: AnyUrl = Field(
        default="http://policy-engine:8000/v1/evaluate", alias="POLICY_ENGINE_URL"
    )
    identity_service_url: AnyUrl = Field(
        default="http://identity-service:8000/v1/tokens/issue", alias="IDENTITY_SERVICE_URL"
    )

    # Notification service used to broadcast orchestration milestones
    notification_service_url: Optional[AnyUrl] = Field(
        default="http://notification-service:8084/v1/notifications",
        alias="NOTIFICATION_SERVICE_URL",
    )

    # Ray runtime (can be local or remote cluster)
    ray_address: Optional[str] = Field(default="auto", alias="RAY_ADDRESS")
    ray_namespace: str = Field(default="somagent", alias="RAY_NAMESPACE")

    # OpenTelemetry exporter (optional)
    otlp_endpoint: Optional[AnyUrl] = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Singleton-style accessor used across the service."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
