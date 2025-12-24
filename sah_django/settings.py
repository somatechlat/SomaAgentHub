"""Django settings for the SomaAgentHub control-plane (Django + Ninja + Channels)."""

from __future__ import annotations

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent


def env(key: str, default: str | None = None, *, required: bool = False) -> str:
    """Fetch an environment variable with optional default and required flag."""
    val = os.getenv(key, default)
    if required and val is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val if val is not None else ""


# Security
SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = env("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "ninja",
    "admin.core",
    "apps.gateway",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.gateway.middleware_auth.AuthMiddleware",
    "apps.gateway.middleware_rbac.RBACMiddleware",
    "apps.gateway.middleware.OPAMiddleware",
]

ROOT_URLCONF = "sah_django.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sah_django.wsgi.application"
ASGI_APPLICATION = "sah_django.asgi.application"

# Database (Postgres)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "somaagenthub"),
        "USER": env("POSTGRES_USER", "soma"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

# Cache / Channels
REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Service URLs (parity with existing FastAPI settings)
ORCHESTRATOR_URL = env("ORCHESTRATOR_URL", "http://orchestrator:8000")
IDENTITY_URL = env("IDENTITY_URL", "http://identity-service:8000")
POLICY_ENGINE_URL = env("POLICY_ENGINE_URL", "http://policy-engine:8000")
MEMORY_GATEWAY_URL = env("MEMORY_GATEWAY_URL", "http://memory-gateway:8000")
LLM_HUB_URL = env("LLM_HUB_URL", "http://llm-hub:8000")
OPA_URL = env("OPA_URL", "http://opa:8181")
OPA_TIMEOUT = float(env("OPA_TIMEOUT", "5.0") or "5.0")

# Deployment context defaults
DEFAULT_TENANT_ID = env("DEFAULT_TENANT_ID", "default-tenant")
DEFAULT_CLIENT_TYPE = env("DEFAULT_CLIENT_TYPE", "api-client")
DEFAULT_DEPLOYMENT_MODE = env("DEFAULT_DEPLOYMENT_MODE", "cluster")

# Message catalog module path (used by endpoints for user-facing strings)
MESSAGE_CATALOG = "admin.common.messages"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
