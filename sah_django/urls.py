"""URL configuration for the SomaAgentHub Django control-plane."""

from __future__ import annotations

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from apps.gateway.api import router as gateway_router

api = NinjaAPI(
    title="SomaAgentHub API",
    version="2.0",
)
api.add_router("", gateway_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", api.urls),
]
