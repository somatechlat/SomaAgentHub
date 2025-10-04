"""Entry point for billing service."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="SomaGent Billing Service",
    version="0.1.0",
    description="Handles subscription management, payment processing, and usage billing.",
)

@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "billing-service"}

@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "SomaGent Billing Service"}

# Billing endpoints
@app.get("/subscriptions", tags=["billing"])
def list_subscriptions():
    return {"subscriptions": []}

@app.post("/subscriptions", tags=["billing"])
def create_subscription(subscription: dict):
    return {"message": "Subscription created", "subscription": subscription}

@app.get("/usage", tags=["billing"])
def get_usage():
    return {"usage": {"tokens": 0, "requests": 0}}