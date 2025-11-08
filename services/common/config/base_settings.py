from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Common base settings for all SomaAgent services.

    Provides shared environment fields (environment, log level, tracing flags) that
    each service can extend. Centralizing here reduces duplication and drift.
    """

    environment: str = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_prometheus: bool = True
    enable_otlp: bool = False  # overridable per environment

    class Config:
        env_prefix = "SOMAGENT_"
        case_sensitive = False


@lru_cache(maxsize=32)
def load_settings(cls: type[BaseServiceSettings]) -> BaseServiceSettings:
    """Load and cache a settings class instance.

    Services call: `settings = load_settings(MyServiceSettings)`.
    """
    # pydantic BaseSettings subclasses are callable with no args to read env.
    instance: BaseServiceSettings = cls()  # construct
    return instance


def apply_log_level(logger_name: str, level: str) -> None:
    import logging

    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(logger_name).setLevel(lvl)
    logging.getLogger().setLevel(lvl)
