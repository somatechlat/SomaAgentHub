"""Gateway service configuration wrapper to core settings."""

# Import the core configuration for the gateway service. The package name uses an
# underscore (`gateway_api`) because hyphens are not valid identifiers in Python
# import statements. The directory on disk is named `gateway-api`; the project
# relies on the namespace package handling in `services/__init__.py` to make
# the import work when the folder name contains a hyphen. We therefore import
# from the underscore‑based module name which resolves correctly via the
# extended path.
from services.gateway_api.app.core.config import (
    GatewaySettings,
    get_settings,
    SERVICE_NAME,
    SERVICE_PORT,
    DATABASE_URL,
    REDIS_URL,
    ORCHESTRATOR_URL,
    PRICING_SERVICE_URL,
    JWT_SECRET,
)

from services.common.config.base_settings import resolve_env

ENVIRONMENT = resolve_env("ENVIRONMENT", "development")
DEPLOYMENT_MODE = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()


def get_service_url(service_name: str):
    # Best-effort mapping via env
    return resolve_env(f"{service_name.upper().replace('-', '_')}_URL") or ""


# Compatibility shim -------------------------------------------------------
def get_sah_settings() -> GatewaySettings:
    """Legacy accessor used by older imports.

    Some modules (e.g., ``services.gateway-api.app.main``) import
    ``get_sah_settings`` expecting it to return the service settings. The new
    configuration provides ``get_settings`` which returns a ``GatewaySettings``
    instance. This wrapper forwards the call to maintain backward compatibility
    without altering existing import sites.
    """
    return get_settings()
