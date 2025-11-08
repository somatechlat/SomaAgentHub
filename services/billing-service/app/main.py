"""Billing Service API.

Provides:
- Health & metrics
- Payment intent creation (Stripe)
- Webhook receiver (Stripe events)
- Usage summary passthrough (from usage tracker)
- Subscription placeholder endpoints (to be extended)

Env expectations:
- STRIPE_SECRET_KEY (secret)
- STRIPE_WEBHOOK_SECRET (optional for verifying signatures)
"""

import os
import logging
from typing import Optional
import stripe
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from datetime import datetime, timedelta

from .usage_tracker import get_usage_tracker

logger = logging.getLogger(__name__)

STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_KEY:
    stripe.api_key = STRIPE_KEY
else:
    logger.warning("STRIPE_SECRET_KEY not set; payment endpoints will fail.")

app = FastAPI(
    title="SomaAgent Billing Service",
    version="0.2.0",
    description="Handles subscription management, payment processing, usage billing, and payment gating.",
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

class PaymentIntentRequest(BaseModel):
    user_id: str = Field(..., description="ID of user initiating build")
    amount_cents: int = Field(..., ge=1, description="Approved amount in cents")
    currency: str = Field("usd", description="3 letter currency code")
    description: Optional[str] = Field(None, description="Human description for invoice line")

class PaymentIntentResponse(BaseModel):
    intent_id: str
    client_secret: Optional[str]
    amount_cents: int
    currency: str
    created_at: datetime

@app.post("/v1/billing/intent", response_model=PaymentIntentResponse, tags=["billing"])
def create_payment_intent(payload: PaymentIntentRequest):
    """Create a Stripe payment intent for a forthcoming build.

    If Stripe key not configured, returns 503.
    """
    if not STRIPE_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    try:
        intent = stripe.PaymentIntent.create(
            amount=payload.amount_cents,
            currency=payload.currency,
            description=payload.description or f"Build approval for {payload.user_id}",
            metadata={"user_id": payload.user_id}
        )
        logger.info(f"Created payment intent {intent.id} for {payload.user_id} amount={payload.amount_cents}")
        return PaymentIntentResponse(
            intent_id=intent.id,
            client_secret=intent.client_secret,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Failed to create payment intent: {e}")
        raise HTTPException(status_code=500, detail="Payment intent creation failed")

class WebhookEvent(BaseModel):
    """Generic wrapper if manual JSON parsing fallback is needed."""
    type: Optional[str] = None
    data: Optional[dict] = None

@app.post("/v1/billing/webhook", tags=["billing"])
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):  # type: ignore
    """Consume Stripe webhook events to finalize payment gating.

    Notes:
    - If STRIPE_WEBHOOK_SECRET set, verify signature; else process blindly.
    - Emits log events; future: persist to audit store and update BuildRun approval state.
    """
    raw_body = await request.body()
    event = None
    if STRIPE_WEBHOOK_SECRET and stripe_signature:
        try:
            event = stripe.Webhook.construct_event(raw_body.decode(), stripe_signature, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        try:
            event = request.json()
        except Exception:
            event = None

    event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", "unknown")
    logger.info(f"Stripe webhook received type={event_type}")
    # TODO: Update BuildRun or user entitlement based on event_type (payment_intent.succeeded, charge.refunded, etc.)
    return {"received": True, "type": event_type}

class UsageSummaryQuery(BaseModel):
    user_id: str
    period_hours: int = Field(24, ge=1, le=744)

@app.post("/v1/billing/usage", tags=["billing"])
def usage_summary(query: UsageSummaryQuery):
    tracker = get_usage_tracker()
    end = datetime.utcnow()
    start = end - timedelta(hours=query.period_hours)
    summary = tracker.get_usage_summary(query.user_id, start, end)
    return summary


# --- Simple plan entitlements (can be externalized later) ---
DEFAULT_PLANS = {
    "free": {"max_concurrent_builds": 1, "features": ["pricing_queries"]},
    "pro": {"max_concurrent_builds": 3, "features": ["pricing_queries", "basic_build"]},
    "enterprise": {"max_concurrent_builds": 10, "features": ["pricing_queries", "basic_build", "priority_queue"]},
}

class EntitlementsRequest(BaseModel):
    plan: str = Field(..., description="Plan name: free|pro|enterprise")

@app.post("/v1/billing/entitlements", tags=["billing"])
def entitlements(req: EntitlementsRequest):
    plan = DEFAULT_PLANS.get(req.plan.lower())
    if not plan:
        raise HTTPException(status_code=404, detail="Unknown plan")
    return {"plan": req.plan.lower(), **plan}