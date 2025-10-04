"""Entry point for settings service."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="SomaGent Settings Service",
    version="0.1.0",
    description="Manages user preferences, system configuration, and feature flags.",
)

@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "settings-service"}

@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "SomaGent Settings Service"}

# Settings endpoints
@app.get("/settings/user/{user_id}", tags=["settings"])
def get_user_settings(user_id: str):
    return {"user_id": user_id, "preferences": {"theme": "dark", "notifications": True}}

@app.put("/settings/user/{user_id}", tags=["settings"])
def update_user_settings(user_id: str, settings: dict):
    return {"message": "Settings updated", "user_id": user_id, "settings": settings}

@app.get("/settings/system", tags=["settings"])
def get_system_settings():
    return {"features": {"advanced_mode": True, "beta_features": False}}