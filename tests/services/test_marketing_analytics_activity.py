import pytest

from services.orchestrator.app.workflows.marketing_activities import analytics_setup_activity


@pytest.mark.asyncio
async def test_analytics_setup_activity_prometheus_and_hints():
    payload = {
        "input": {
            "campaign_id": "cmp-123",
            "campaign_name": "World Launch",
            "channels": ["email", "blog"],
            "metrics": ["impressions", "clicks"],
        }
    }

    result = await analytics_setup_activity(payload)

    assert result["metric"] == "campaign_analytics_created_total"
    assert result["labels"]["campaign_id"] == "cmp-123"
    assert "metrics_query_hint" in result
    assert "logs_label_hint" in result