"""Configuration primitives for the orchestrator service.

This module centralises environment-driven configuration so both the FastAPI
application and Temporal workers consume the same values.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from the environment."""

    service_name: str = Field(default="orchestrator-service")

    # Temporal configuration
    # Accept TEMPORAL_HOST (preferred) with fallback to legacy TEMPORAL_TARGET_HOST
    temporal_target_host: str = Field(default="localhost:7233", alias="TEMPORAL_HOST")
    temporal_namespace: str = Field(default="default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field(default="somagent.session.workflows", alias="TEMPORAL_TASK_QUEUE")
    temporal_enabled: bool = Field(default=False, alias="TEMPORAL_ENABLED")

    # Kafka audit stream
    kafka_bootstrap_servers: Optional[str] = Field(default=None, alias="KAFKA_BOOTSTRAP_SERVERS")

    # Policy & identity services (real HTTP endpoints)
    policy_engine_url: AnyUrl = Field(
        default=os.getenv("POLICY_ENGINE_URL", "http://policy-engine:10020") + "/v1/evaluate", alias="POLICY_ENGINE_URL"
    )
    identity_service_url: AnyUrl = Field(
        default=os.getenv("IDENTITY_TOKEN_ISSUE_URL", "http://identity-service:10002/v1/tokens/issue"), alias="IDENTITY_SERVICE_URL"
    )

    # Notification service used to broadcast orchestration milestones
    notification_service_url: Optional[AnyUrl] = Field(
        default=os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:10026") + "/v1/notifications",
        alias="NOTIFICATION_SERVICE_URL",
    )

    # SLM service (formerly SomaLLM provider)
    # Default to in-cluster DNS for slm-service on port 1001
    somallm_provider_url: AnyUrl = Field(
        default=os.getenv("SLM_SERVICE_URL", "http://slm-service:10022"),
        alias="SOMALLM_PROVIDER_URL",
    )
    somallm_provider_health_url: AnyUrl = Field(
        default=os.getenv("SLM_HEALTH_URL", "http://slm-service:10022/health"),
        alias="SOMALLM_PROVIDER_HEALTH_URL",
    )

    # Volcano scheduler integration (optional)
    enable_volcano_scheduler: bool = Field(default=False, alias="ENABLE_VOLCANO_SCHEDULER")
    volcano_namespace: str = Field(default="soma-agent-hub", alias="VOLCANO_NAMESPACE")
    volcano_default_queue: str = Field(default="interactive", alias="VOLCANO_DEFAULT_QUEUE")
    volcano_session_image: str = Field(default="python:3.11-slim", alias="VOLCANO_SESSION_IMAGE")
    volcano_session_cpu: str = Field(default="500m", alias="VOLCANO_SESSION_CPU")
    volcano_session_memory: str = Field(default="512Mi", alias="VOLCANO_SESSION_MEMORY")
    volcano_job_timeout_seconds: int = Field(default=300, alias="VOLCANO_JOB_TIMEOUT_SECONDS")
    kubectl_binary: str = Field(default="kubectl", alias="KUBECTL_BINARY")

    # Constitution service manifest signing
    constitution_service_url: AnyUrl = Field(
        default=os.getenv("CONSTITUTION_SERVICE_URL", "http://constitution-service:10024") + "/v1",
        alias="CONSTITUTION_SERVICE_URL",
    )
    manifest_signing_enabled: bool = Field(
        default=True,
        alias="MANIFEST_SIGNING_ENABLED",
    )
    manifest_signing_timeout_seconds: float = Field(
        default=10.0,
        alias="MANIFEST_SIGNING_TIMEOUT_SECONDS",
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
        "extra": "ignore",
    }

    def model_post_init(self, __context) -> None:
        # Support legacy SLM environment variables for backwards compatibility.
        legacy_base = os.getenv("SLM_SERVICE_URL")
        legacy_health = os.getenv("SLM_HEALTH_URL")
        if legacy_base and not os.getenv("SOMALLM_PROVIDER_URL"):
            object.__setattr__(self, "somallm_provider_url", legacy_base)
        if legacy_health and not os.getenv("SOMALLM_PROVIDER_HEALTH_URL"):
            object.__setattr__(self, "somallm_provider_health_url", legacy_health)

        # Backward compatibility for Temporal host env var name
        legacy_temporal = os.getenv("TEMPORAL_TARGET_HOST")
        if legacy_temporal and not os.getenv("TEMPORAL_HOST"):
            object.__setattr__(self, "temporal_target_host", legacy_temporal)
        super().model_post_init(__context)


@lru_cache
def get_settings() -> Settings:
    """Singleton-style accessor used across the service."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
