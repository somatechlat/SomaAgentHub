"""Configuration for analytics service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "analytics-service"
    debug: bool = False
    anomaly_threshold: float = 0.75  # minimal success rate threshold
    regression_interval_hours: int = 24
    billing_default_currency: str = "USD"
    billing_alert_threshold: float = 500.0  # cost alert in default currency
    benchmark_latency_target_ms: float = 1500.0
    benchmark_throughput_target_rps: float = 50.0
    benchmark_error_budget: float = 0.02
    model_config = SettingsConfigDict(env_prefix="SOMAGENT_ANALYTICS_", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
