from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

# ``BaseSettings`` moved to ``pydantic-settings`` in v2. Import with fallback.
try:
	from pydantic import BaseSettings, Field  # type: ignore
 except ImportError:  # pragma: no cover
	from pydantic_settings import BaseSettings  # type: ignore
	from pydantic import Field  # type: ignore


 class BaseServiceSettings(BaseSettings):
	"""Canonical base settings (no duplication, no mocks).

	Only two deployment modes: DEV and PROD. All environment-derived values
	must use the standardized prefix `SOMA_AGENT_HUB_`.
	"""

	environment: str = "development"
	deployment_mode: Literal["DEV", "PROD"] = "DEV"
	log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
	enable_tracing: bool = True
	enable_metrics: bool = True
	enable_prometheus: bool = True
	enable_otlp: bool = False  # overridable per environment

	# Database connection string (supports both SOMA_AGENT_HUB_DATABASE_URL
	# and plain DATABASE_URL for local development).
	database_url: str | None = Field(default=None, env="DATABASE_URL")

	class Config:
		env_prefix = "SOMA_AGENT_HUB_"
		case_sensitive = False

	@property
	def is_dev(self) -> bool:
		return self.deployment_mode == "DEV"

	@property
	def is_prod(self) -> bool:
		return self.deployment_mode == "PROD"


  def resolve_env(name: str, default: Any | None = None) -> Any:
	"""Resolve an environment variable using ONLY the canonical prefix.

	Reads `SOMA_AGENT_HUB_<NAME>` and returns its value if present,
	otherwise returns `default`.
	"""
	import os as _os

	key = f"SOMA_AGENT_HUB_{name}"
	return _os.environ.get(key, default)


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
