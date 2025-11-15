"""SQLModel definitions for the Billing Service.

Only a minimal set of tables is required for the current sprint:

* ``Receipt`` – stores the outcome of a Stripe payment intent.

The model lives in the billing‑service package but re‑uses the shared
PostgreSQL connection utilities from the orchestrator service (`get_async_session`).
All fields are typed to allow SQLModel to generate the appropriate PostgreSQL
schema via Alembic (migration scaffolding is outside the scope of this patch).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ReceiptStatus(str, enum.Enum):
    """Possible states of a payment receipt."""

    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Receipt(SQLModel, table=True):
    __tablename__ = "billing_receipts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, description="User identifier from the payment request")
    stripe_payment_intent_id: str = Field(index=True, description="Stripe PaymentIntent ID")
    amount_cents: int = Field(description="Amount in cents")
    currency: str = Field(max_length=3, description="ISO currency code")
    status: ReceiptStatus = Field(default=ReceiptStatus.PENDING, description="Current receipt status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Timestamp of last status change")


class BudgetDecision(SQLModel, table=True):
    """Result of a budget evaluation for a user request.

    Stored so that downstream services (or audit logs) can reference the exact
    decision that was made at build time.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(index=True, description="User that requested the budget check")
    within_budget: bool = Field(description="True if estimated cost fits the budget cap")
    estimated_cost: float = Field(description="Estimated cost in the requested currency")
    currency: str = Field(max_length=3, description="ISO currency code")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
