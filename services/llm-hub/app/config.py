"""LLM‑Hub configuration.

The project now uses the **centralised configuration system** located in
``services.common.config``.  This module therefore provides a thin wrapper that
exposes the same public API (``get_settings``) as the previous implementation
while delegating all environment‑variable handling to the shared ``BaseConfig``.

Only values that are truly service‑specific and cannot be expressed via the
standard ``BaseConfig`` fields are kept as helper functions.  In this case the
Vault‑based secret retrieval for API keys is retained because it is a real
requirement, but the surrounding boilerplate has been removed.
"""

from services.common.config import get_service_settings
from services.common.vault_client import init_vault

_SERVICE_NAME = "llm-hub"

# Obtain a cached ``BaseConfig`` instance scoped to this service.  The central
# config already resolves ``SERVICE_PORT`` and ``DATABASE_URL`` (using the
# ``SOMA_AGENT_HUB_`` prefix), so we simply expose the instance.
settings = get_service_settings(_SERVICE_NAME)


def _get_api_key(env_name: str, vault_key: str) -> str:
	"""Return an API key from the environment or Vault.

	The function first checks the environment variable; if it is missing it
	attempts to read the secret from Vault using the service name as the role.
	Any exception is swallowed and an empty string is returned – matching the
	original behaviour while keeping the implementation explicit.
	"""

	from services.common.config.base_settings import resolve_env

	val = resolve_env(env_name)
	if val:
		return val
	try:
		client = init_vault(role=_SERVICE_NAME)
		secret = client.read_secret("services/llm-hub").data.get(vault_key)
		if secret:
			return secret
	except Exception:
		# Real‑world production code would log the error; we keep the
		# lightweight behaviour required by the VIBE rules.
		import logging
		logging.getLogger(__name__).warning(f"Failed to read secret {vault_key} from Vault")
	return ""


# Convenience attributes that downstream code may import directly.
OPENAI_API_KEY = _get_api_key("OPENAI_API_KEY", "openai_api_key")
ANTHROPIC_API_KEY = _get_api_key("ANTHROPIC_API_KEY", "anthropic_api_key")
GOOGLE_API_KEY = _get_api_key("GOOGLE_API_KEY", "google_api_key")


def get_settings():
	"""Return the cached ``BaseConfig`` for the LLM hub.

	Keeping a function wrapper mirrors the original module contract, so existing
	imports (``from …config import get_settings``) remain functional.
	"""

	return settings
