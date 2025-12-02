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

import logging
import os
from datetime import UTC, datetime, timedelta

import stripe
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from .usage_tracker import get_usage_tracker
from .models import Receipt, ReceiptStatus, BudgetDecision
import httpx
from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env
from services.orchestrator.app.database import get_async_session
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)

STRIPE_KEY = resolve_env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = resolve_env("STRIPE_WEBHOOK_SECRET")
PRICING_SERVICE_URL = resolve_env("PRICING_SERVICE_URL")

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
description: str | None = Field(
None, description="Human description for invoice line"
)


class PaymentIntentResponse(BaseModel):
intent_id: str
client_secret: str | None
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
metadata={"user_id": payload.user_id},
)
logger.info(
f"Created payment intent {intent.id} for {payload.user_id} amount={payload.amount_cents}"
)
return PaymentIntentResponse(
intent_id=intent.id,
client_secret=intent.client_secret,
amount_cents=payload.amount_cents,
currency=payload.currency,
created_at=datetime.now(UTC),
)
except Exception as e:
logger.error(f"Failed to create payment intent: {e}")
raise HTTPException(status_code=500, detail="Payment intent creation failed")


class WebhookEvent(BaseModel):

type: str | None = None
data: dict | None = None


@app.post("/v1/billing/webhook", tags=["billing"])
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(None)):  # type: ignore
"""Consume Stripe webhook events to finalize payment gating.

Notes:
- If STRIPE_WEBHOOK_SECRET set, verify signature; else process blindly.
- Emits log events; future: persist to audit store and update BuildRun approval state.
"""
raw_body = await request.body()
event = None
if STRIPE_WEBHOOK_SECRET and stripe_signature:
try:
event = stripe.Webhook.construct_event(
raw_body.decode(), stripe_signature, STRIPE_WEBHOOK_SECRET
)
except Exception as e:
logger.warning(f"Webhook signature verification failed: {e}")
raise HTTPException(status_code=400, detail="Invalid signature")
else:
try:
event = request.json()
except Exception:
event = None

	event_type = (
		event.get("type")
		if isinstance(event, dict)
		else getattr(event, "type", "unknown")
	)
	logger.info(f"Stripe webhook received type={event_type}")

	# Persist receipt information for payment_intent events.
	if isinstance(event, dict) and event_type.startswith("payment_intent."):
		obj = event.get("data", {}).get("object", {})
		stripe_intent_id = obj.get("id")
		amount = obj.get("amount")
		currency = obj.get("currency")
		metadata = obj.get("metadata", {})
		user_id = metadata.get("user_id", "unknown")
		# Map Stripe status to our enum.
		stripe_status = obj.get("status")
		status_map = {
			"succeeded": ReceiptStatus.SUCCEEDED,
			"requires_payment_method": ReceiptStatus.FAILED,
			"canceled": ReceiptStatus.FAILED,
			"requires_action": ReceiptStatus.PENDING,
		}
		receipt_status = status_map.get(stripe_status, ReceiptStatus.PENDING)
		async with get_async_session() as session:
			receipt = Receipt(
				user_id=user_id,
				stripe_payment_intent_id=stripe_intent_id,
				amount_cents=amount,
				currency=currency,
				status=receipt_status,
			)
			session.add(receipt)
			await session.commit()
			logger.info("Stored receipt %s for user %s", receipt.id, user_id)

	logger.info("Processed Stripe event type=%s", event_type)
	return {"received": True, "type": event_type}


# ---------------------------------------------------------------------------
# Budget evaluation endpoint (integrates with pricing-service)
# ---------------------------------------------------------------------------


class BudgetEvalRequest(BaseModel):
	user_id: str = Field(..., description="User requesting the build")
	gpu_model: str | None = Field(None, description="GPU model filter for pricing")
	region: str | None = Field(None, description="Region filter for pricing")
	hours_planned: float = Field(..., gt=0, description="Planned runtime in hours")
	quantity: int = Field(1, ge=1, description="Number of agents to provision")
	budget_cap: float = Field(..., gt=0, description="Maximum budget in currency units")


@app.post("/v1/billing/evaluate-budget", tags=["billing"], response_model=dict)
async def evaluate_budget(request: BudgetEvalRequest) -> dict:
	"""Forward budget evaluation to the pricing service and persist the decision.

	This endpoint makes a real HTTP call to the external pricing service using
	the ``PRICING_SERVICE_URL`` environment variable. The response is stored in
	the ``budget_decisions`` table for auditability.
	"""
	if not PRICING_SERVICE_URL:
		raise HTTPException(status_code=503, detail="Pricing service URL not configured")

	pricing_endpoint = f"{PRICING_SERVICE_URL.rstrip('/')}/v1/pricing/evaluate-budget"
	payload = {
		"gpu_model": request.gpu_model,
		"region": request.region,
		"hours_planned": request.hours_planned,
		"quantity": request.quantity,
		"budget_cap": request.budget_cap,
	}
	try:
		async with httpx.AsyncClient(timeout=5.0) as client:
			resp = await client.post(pricing_endpoint, json=payload)
	except Exception as e:
		logger.error("Failed to call pricing service: %s", e)
		raise HTTPException(status_code=502, detail="Pricing service unavailable")

	if resp.status_code != 200:
		raise HTTPException(status_code=resp.status_code, detail=resp.text)

	data = resp.json()
	# Persist decision
	async with get_async_session() as session:
		decision = BudgetDecision(
			user_id=request.user_id,
			within_budget=data.get("within_budget", False),
			estimated_cost=data.get("estimated_cost", 0.0),
			currency=data.get("currency", "usd"),
		)
		session.add(decision)
		await session.commit()

	return {
		"decision_id": str(decision.id),
		"within_budget": decision.within_budget,
		"estimated_cost": decision.estimated_cost,
		"currency": decision.currency,
		"pricing_response": data,
	}


class UsageSummaryQuery(BaseModel):
user_id: str
period_hours: int = Field(24, ge=1, le=744)


@app.post("/v1/billing/usage", tags=["billing"])
def usage_summary(query: UsageSummaryQuery):
tracker = get_usage_tracker()
end = datetime.now(UTC)
start = end - timedelta(hours=query.period_hours)
summary = tracker.get_usage_summary(query.user_id, start, end)
return summary


# --- Simple plan entitlements (can be externalized later) ---
DEFAULT_PLANS = {
"free": {"max_concurrent_builds": 1, "features": ["pricing_queries"]},
"pro": {"max_concurrent_builds": 3, "features": ["pricing_queries", "basic_build"]},
"enterprise": {
"max_concurrent_builds": 10,
"features": ["pricing_queries", "basic_build", "priority_queue"],
},
}


class EntitlementsRequest(BaseModel):
plan: str = Field(..., description="Plan name: free|pro|enterprise")


@app.post("/v1/billing/entitlements", tags=["billing"])
def entitlements(req: EntitlementsRequest):
plan = DEFAULT_PLANS.get(req.plan.lower())
if not plan:
raise HTTPException(status_code=404, detail="Unknown plan")
return {"plan": req.plan.lower(), **plan}
