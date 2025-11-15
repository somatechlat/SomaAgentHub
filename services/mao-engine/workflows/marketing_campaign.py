"""
Marketing Campaign Workflow - Unified MAO Engine Implementation.

Migrated from services/orchestrator/app/workflows/marketing_campaign.py
to demonstrate unified workflow implementation with proven patterns.

TRUTH: This workflow demonstrates the unified approach with MAO engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from temporalio import workflow

from services.mao_engine.core import (
workflow_registry,
WorkflowType,
WorkflowStatus,
)
from services.mao_engine.core.patterns.saga import SagaBuilder


@dataclass
class MarketingCampaignParams:
"""Parameters for marketing campaign workflow."""

campaign_id: str
budget: float
target_audience: Dict[str, Any]
campaign_duration_days: int
channels: list[str]


@dataclass
class MarketingCampaignResult:
"""Result from marketing campaign workflow."""

campaign_id: str
status: str
budget_allocated: float
campaigns_created: list[str]
notifications_sent: int
tracking_setup: bool
error_message: str | None = None


@workflow_registry.register_workflow(
name="marketing_campaign",
workflow_type=WorkflowType.SAGA,
description="End-to-end marketing campaign orchestration using proven saga pattern",
timeout_seconds=3600,
tags=["marketing", "campaign", "saga"],
)
@workflow.defn
class MarketingCampaignWorkflow:
"""
Marketing Campaign Workflow - Unified MAO Engine Implementation.

TRUTH: This workflow demonstrates the unified approach:
- Uses centralized workflow registry
- Implements proven saga pattern
- Leverages unified activity registry
- Consistent with all other workflows

Original Implementation:
This workflow was originally implemented in services/orchestrator/app/workflows/marketing_campaign.py
and has been migrated to demonstrate the unified MAO engine approach.

Usage:
params = MarketingCampaignParams(
    campaign_id="campaign-123",
    budget=10000.0,
    target_audience={"segment": "premium", "size": 1000},
    campaign_duration_days=30,
    channels=["email", "social", "display"]
)

result = await mao_engine.execute_saga(
    workflow_id="campaign-123",
    workflow_name="marketing_campaign",
    input_data=params.__dict__
)
"""

def __init__(self) -> None:
"""Initialize workflow."""
self._saga_builder = SagaBuilder()

@workflow.run
async def run(self, params: MarketingCampaignParams) -> MarketingCampaignResult:
"""
Execute marketing campaign workflow using saga pattern.

Args:
params: Campaign parameters

Returns:
Campaign execution result
"""
try:
# Build saga with compensation steps
saga = (
self._saga_builder
# Step 1: Allocate budget (compensation: release budget)
.step(
activity="allocate_budget",
compensation="release_budget",
input_data={
"campaign_id": params.campaign_id,
"budget": params.budget,
},
)
# Step 2: Create campaign assets (compensation: delete assets)
.step(
activity="create_campaign_assets",
compensation="delete_campaign_assets",
input_data={
"campaign_id": params.campaign_id,
"channels": params.channels,
"target_audience": params.target_audience,
},
)
# Step 3: Schedule campaigns (compensation: cancel campaigns)
.step(
activity="schedule_campaigns",
compensation="cancel_campaigns",
input_data={
"campaign_id": params.campaign_id,
"channels": params.channels,
"duration_days": params.campaign_duration_days,
},
)
# Step 4: Send notifications (compensation: cancel notifications)
.step(
activity="send_notifications",
compensation="cancel_notifications",
input_data={
"campaign_id": params.campaign_id,
"target_audience": params.target_audience,
"channels": params.channels,
},
)
# Step 5: Setup tracking (compensation: remove tracking)
.step(
activity="setup_tracking",
compensation="remove_tracking",
input_data={
"campaign_id": params.campaign_id,
"channels": params.channels,
},
)
.build()
)

# Execute saga
result = await saga.execute()

# Create final result
campaign_result = MarketingCampaignResult(
campaign_id=params.campaign_id,
status="completed",
budget_allocated=result.get("budget_allocated", 0.0),
campaigns_created=result.get("campaigns_created", []),
notifications_sent=result.get("notifications_sent", 0),
tracking_setup=result.get("tracking_setup", False),
)

return campaign_result

except Exception as e:
# Return error result
return MarketingCampaignResult(
campaign_id=params.campaign_id,
status="failed",
budget_allocated=0.0,
campaigns_created=[],
notifications_sent=0,
tracking_setup=False,
error_message=str(e),
)


# Register the workflow class with Temporal
# This is needed for Temporal to discover the workflow
workflow.register(MarketingCampaignWorkflow)