"""Gateway service configuration wrapper.

This module now delegates all configuration handling to the **central
configuration system** located in ``services.common.config``.  Previously the
gateway imported a service‑specific ``GatewaySettings`` class from its own
``core.config`` module, which duplicated a large amount of logic already
provided by the central ``BaseConfig`` hierarchy.

By using :func:`services.common.config.get_service_settings` we obtain a
fully‑validated ``BaseConfig`` instance with ``service_name`` set to
``"gateway-api"``.  The returned object contains all common settings (database
URL, Redis URL, JWT secret, etc.) as well as service‑specific fields such as
``service_version``.

Only a small compatibility shim ``get_service_url`` is retained for legacy
code that expects a simple environment‑variable lookup.
"""

from __future__ import annotations

"""Gateway service configuration.

The gateway needs a handful of service URLs (orchestrator, identity, pricing,
policy, memory‑gateway, llm‑hub) as well as generic settings such as the
environment and deployment mode.  Rather than duplicating logic, we build a
lightweight ``GatewaySettings`` class that extends the central ``BaseConfig``
and pulls the required values from environment variables using the shared
``resolve_env`` helper.

Existing code imports ``GatewaySettings`` and ``get_settings`` from this module,
so we preserve that public API.
"""

from services.common.config.base_settings import BaseServiceSettings, resolve_env


class GatewaySettings(BaseServiceSettings):
	"""Configuration specific to the Gateway service.

	Only the fields required by the current code base are defined.  All other
	values are inherited from ``BaseServiceSettings`` (environment, deployment
	mode, etc.).
	"""

	# Service URLs – fall back to the historic defaults used throughout the
	# repository.
	orchestrator_url: str = resolve_env(
		"ORCHESTRATOR_URL", "http://orchestrator:8000"
	)
	auth_url: str = resolve_env("IDENTITY_URL", "http://identity-service:8000")
	pricing_service_url: str = resolve_env(
		"PRICING_SERVICE_URL", "http://pricing-service:8000"
	)
	policy_engine_url: str = resolve_env(
		"POLICY_ENGINE_URL", "http://policy-engine:8000"
	)
	memory_gateway_url: str = resolve_env(
		"MEMORY_GATEWAY_URL", "http://memory-gateway:8000"
	)
	llm_hub_url: str = resolve_env("LLM_HUB_URL", "http://llm-hub:8000")


# Export a singleton instance to match the original module contract.
settings = GatewaySettings()


def get_settings() -> GatewaySettings:
	"""Return the cached ``GatewaySettings`` instance.

	Keeping a function wrapper mirrors the pattern used by other services and
	allows lazy imports without side effects.
	"""

	return settings


 def get_service_url(service_name: str) -> str:
	"""Legacy helper – returns ``SOMA_AGENT_HUB_<NAME>_URL`` if set.
	"""

	return resolve_env(f"{service_name.upper().replace('-', '_')}_URL") or ""

