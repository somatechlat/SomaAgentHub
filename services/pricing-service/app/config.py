"""Pricing‑service configuration.

The project now uses a **centralised configuration system** located in
``services.common.config``.  Each service obtains a scoped ``BaseConfig``
instance via ``get_service_settings(service_name)``.  This file therefore
exposes a thin wrapper that returns the shared settings object for the
``pricing-service``.

Why this works
--------------
* All environment‑variable parsing, validation and defaults are defined once
  in ``services/common/config/base_settings.py``.
* ``get_service_settings`` caches the result (via ``functools.lru_cache``),
  so the settings object is a singleton per service – matching the previous
  ``@lru_cache`` behaviour.
* Existing code that imports ``get_settings`` continues to function unchanged.
"""

from services.common.config import get_service_settings

# The service name used for environment‑variable prefixes (e.g. ``PRICING_…``).
_SERVICE_NAME = "pricing-service"

# Obtain a cached ``BaseConfig`` instance scoped to this service.
settings = get_service_settings(_SERVICE_NAME)


def get_settings():
	"""Return the cached ``BaseConfig`` for the pricing service.

	The function signature mirrors the previous implementation so callers do
	not need to be updated.
	"""

	return settings
