        ng Service API.

        :
            alth & metrics
            yment intent creation (Stripe)
            bhook receiver (Stripe events)
            age summary passthrough (from usage tracker)
            bscription placeholder endpoints (to be extended)

            expectations:
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
                    pe.api_key = STRIPE_KEY
                    :
                        er.warning("STRIPE_SECRET_KEY not set; payment endpoints will fail.")

                        = FastAPI(
                        e="SomaAgent Billing Service",
                        ion="0.2.0",
                        ription="Handles subscription management, payment processing, usage billing, and payment gating.",
                        )


                        .get("/health", tags=["system"])
                        healthcheck() -> dict[str, str]:
                            return {"status": "ok", "service": "billing-service"}


                            @app.get("/metrics", tags=["system"])
                            def metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


            @app.get("/")
            def root():
                return {"message": "SomaGent Billing Service"}


                g endpoints
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

                                                                                ype = (
                                                                                get("type")
                                                                                nstance(event, dict)
                                                                                etattr(event, "type", "unknown")
                                                                                )
                                                                                info(f"Stripe webhook received type={event_type}")

                                                                                st receipt information for payment_intent events.
                                                                                stance(event, dict) and event_type.startswith("payment_intent."):
                                                                                    event.get("data", {}).get("object", {})
                                                                                    _intent_id = obj.get("id")
         = obj.get("amount")
         cy = obj.get("currency")
         ta = obj.get("metadata", {})
         d = metadata.get("user_id", "unknown")
         Stripe status to our enum.
         _status = obj.get("status")
         _map = {
         eeded": ReceiptStatus.SUCCEEDED,
         ires_payment_method": ReceiptStatus.FAILED,
         eled": ReceiptStatus.FAILED,
         ires_action": ReceiptStatus.PENDING,
         }
         t_status = status_map.get(stripe_status, ReceiptStatus.PENDING)
         with get_async_session() as session:
             pt = Receipt(
             _id=user_id,
             pe_payment_intent_id=stripe_intent_id,
             nt_cents=amount,
             ency=currency,
             us=receipt_status,
             )
             on.add(receipt)
         session.commit()
         r.info("Stored receipt %s for user %s", receipt.id, user_id)

         info("Processed Stripe event type=%s", event_type)
         {"received": True, "type": event_type}


         ---------------------------------------------------------------------
         evaluation endpoint (integrates with pricing-service)
         ---------------------------------------------------------------------


         udgetEvalRequest(BaseModel):
             : str = Field(..., description="User requesting the build")
             el: str | None = Field(None, description="GPU model filter for pricing")
         str | None = Field(None, description="Region filter for pricing")
         lanned: float = Field(..., gt=0, description="Planned runtime in hours")
         y: int = Field(1, ge=1, description="Number of agents to provision")
         cap: float = Field(..., gt=0, description="Maximum budget in currency units")


         st("/v1/billing/evaluate-budget", tags=["billing"], response_model=dict)
         ef evaluate_budget(request: BudgetEvalRequest) -> dict:
             ard budget evaluation to the pricing service and persist the decision.

             dpoint makes a real HTTP call to the external pricing service using
             RICING_SERVICE_URL`` environment variable. The response is stored in
             udget_decisions`` table for auditability.
             """
             PRICING_SERVICE_URL:
                 HTTPException(status_code=503, detail="Pricing service URL not configured")

                 _endpoint = f"{PRICING_SERVICE_URL.rstrip('/')}/v1/pricing/evaluate-budget"
         = {
         odel": request.gpu_model,
         n": request.region,
         _planned": request.hours_planned,
         ity": request.quantity,
         t_cap": request.budget_cap,
         }
         try:
             with httpx.AsyncClient(timeout=5.0) as client:
                 = await client.post(pricing_endpoint, json=payload)
                 Exception as e:
                     .error("Failed to call pricing service: %s", e)
                     HTTPException(status_code=502, detail="Pricing service unavailable")

                     .status_code != 200:
                         HTTPException(status_code=resp.status_code, detail=resp.text)

                         resp.json()
                         st decision
                         ith get_async_session() as session:
                             on = BudgetDecision(
                             id=request.user_id,
                             n_budget=data.get("within_budget", False),
                             ated_cost=data.get("estimated_cost", 0.0),
                             ncy=data.get("currency", "usd"),
                             )
                             n.add(decision)
                             session.commit()

                             {
                             ion_id": str(decision.id),
                             n_budget": decision.within_budget,
                             ated_cost": decision.estimated_cost,
                             ncy": decision.currency,
                             ng_response": data,
                             }


                             sageSummaryQuery(BaseModel):
                                 r_id: str
                                 iod_hours: int = Field(24, ge=1, le=744)


                                 p.post("/v1/billing/usage", tags=["billing"])
         usage_summary(query: UsageSummaryQuery):
         tracker = get_usage_tracker()
         end = datetime.now(UTC)
         start = end - timedelta(hours=query.period_hours)
         summary = tracker.get_usage_summary(query.user_id, start, end)
         return summary


         mple plan entitlements (can be externalized later) ---
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
