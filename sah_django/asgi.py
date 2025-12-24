"""ASGI config for SomaAgentHub Django control-plane."""

from __future__ import annotations

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sah_django.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # WebSocket routes can be added to this URLRouter as they are implemented.
        "websocket": URLRouter([]),
    }
)
