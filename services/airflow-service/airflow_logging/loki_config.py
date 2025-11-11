import os
from services.common.config.base_settings import resolve_env

# Airflow expects a dict named LOGGING_CONFIG when using custom logging config class path
LOKI_URL = resolve_env("LOKI_URL", "http://loki.observability:3100")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "loki": {
            "class": "logging_loki.LokiHandler",
            "level": "INFO",
            "formatter": "default",
            "url": f"{LOKI_URL}/loki/api/v1/push",
            "tags": {"service": "airflow"},
            "version": "1",
        }
    },
    "root": {"handlers": ["loki"], "level": "INFO"},
}
