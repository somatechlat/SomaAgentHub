"""Memory‑gateway configuration.

The service now uses the **central configuration system** (`services.common.config`).
We keep the Vault‑based secret retrieval for the Qdrant API key because that is a
real requirement that cannot be expressed via plain environment variables.
All other settings are obtained from the shared ``BaseConfig`` instance.
"""

from services.common.config import get_service_settings
from services.common.vault_client import init_vault

_SERVICE_NAME = "memory-gateway"

# Cached ``BaseConfig`` scoped to this service.
settings = get_service_settings(_SERVICE_NAME)


def _get_qdrant_api_key() -> str:
	"""Retrieve the Qdrant API key from the environment or Vault.

	The function first checks ``QDRANT_API_KEY``; if missing it attempts to read
	the secret from Vault using the service name as the role.  Any exception is
	swallowed and an empty string is returned – matching the original behaviour.
	"""
	from services.common.config.base_settings import resolve_env

	val = resolve_env("QDRANT_API_KEY")
	if val:
		return val
	try:
		client = init_vault(role=_SERVICE_NAME)
		secret = client.read_secret("services/memory-gateway").data.get(
			"qdrant_api_key"
		)
		if secret:
			return secret
	except Exception:
		pass
	return ""


# Convenience constants derived from the central ``settings`` object.
SERVICE_PORT = int(getattr(settings, "service_port", 8082))
DATABASE_URL = getattr(settings, "database_url", "postgresql://postgres:postgres@postgres:5432/soma")
REDIS_URL = getattr(settings, "redis_url", "redis://redis:6379/0")
QDRANT_URL = getattr(settings, "qdrant_url", "http://localhost:6333")
QDRANT_API_KEY = _get_qdrant_api_key()
OBJECT_STORE_BUCKET = getattr(settings, "object_store_bucket", "")
OBJECT_STORE_REGION = getattr(settings, "object_store_region", "")
ENVIRONMENT = getattr(settings, "environment", "development")
DEPLOYMENT_MODE = getattr(settings, "deployment_mode", "DEV").upper()


def get_service_url(service_name: str) -> str:
	"""Return a URL for a dependent service using the central resolver.
	"""
	key = f"{service_name.upper().replace('-', '_')}_URL"
	return getattr(settings, key.lower(), f"http://{service_name}")


def get_env_var(name: str, default=None):
	"""Thin wrapper around the central ``resolve_env``.
	"""
	return getattr(settings, name.lower(), default)


class MemoryGatewayConfig:
	"""Configuration class for the memory‑gateway service.

	Mirrors the original public API while sourcing all values from the cached
	``settings`` instance.
	"""

	@classmethod
	def from_env(cls):
		return cls()

	def __init__(self):
		self.qdrant_url = QDRANT_URL
		self.qdrant_api_key = QDRANT_API_KEY
		self.database_url = DATABASE_URL
		self.redis_url = REDIS_URL
		self.bucket_name = OBJECT_STORE_BUCKET
		self.region = OBJECT_STORE_REGION


def get_settings():
	"""Return the cached ``BaseConfig`` for the memory‑gateway.
	"""
	return settings
