"""WSGI config for SomaAgentHub Django control-plane."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sah_django.settings")

application = get_wsgi_application()
