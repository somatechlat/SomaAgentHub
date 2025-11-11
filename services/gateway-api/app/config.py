"""Gateway service configuration wrapper to core settings."""

# Import the core configuration for the gateway service. The package name uses an
# underscore (`gateway_api`) because hyphens are not valid identifiers in Python
# import statements. The directory on disk is named `gateway-api`; the project
# relies on the namespace package handling in `services/__init__.py` to make
# the import work when the folder name contains a hyphen. We therefore import
# from the underscore‑based module name which resolves correctly via the
# extended path.
from services.gateway_api.app.core.config import GatewaySettings, get_settings

from services.common.config.base_settings import resolve_env

ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()


def get_service_url(service_name: str):
# Best-effort mapping via env
return resolve_env(f"{service_name.upper().replace('-', '_')}_URL") or ""


# (Shim removed - use get_settings directly from core.config)
