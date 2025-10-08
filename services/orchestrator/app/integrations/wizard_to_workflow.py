"""
Integration module: Gateway API → Temporal Orchestrator.

Connects wizard approval to MarketingCampaignWorkflow execution.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from temporalio import client as temporal_client


async def start_marketing_campaign_workflow(
    temporal_client: temporal_client.Client,
    wizard_session: Dict[str, Any],
    task_queue: str = "somagent-tasks",
) -> Dict[str, Any]:
    """
    Start MarketingCampaignWorkflow from wizard approval.
    
    Args:
        temporal_client: Temporal client instance
        wizard_session: Wizard session with user answers
        task_queue: Temporal task queue name
        
    Returns:
        {
            "workflow_id": "campaign-...",
            "run_id": "...",
            "campaign_id": "..."
        }
    """
    answers = wizard_session.get("answers", {})
    
    # Extract campaign parameters from wizard answers
    campaign_name = answers.get("campaign_name", "Untitled Campaign")
    campaign_goals = answers.get("campaign_goals", [])
    target_audience = answers.get("target_audience", "")
    budget = float(answers.get("budget", 10000))
    
    # Extract channel selection
    channels = []
    if answers.get("email_channel"):
        channels.append("email")
    if answers.get("social_channel"):
        channels.append("social")
    if answers.get("blog_channel"):
        channels.append("blog")
    
    # Extract research parameters
    research_sources = answers.get("research_sources", ["notion"])
    competitor_urls = answers.get("competitor_urls", "").split("\n") if answers.get("competitor_urls") else []
    
    # Extract content parameters
    tone = answers.get("tone", "professional")
    brand_voice_id = answers.get("brand_voice_id")
    
    # Build workflow input
    from ..workflows.marketing_campaign import CampaignInput
    
    campaign_input = CampaignInput(
        campaign_name=campaign_name,
        campaign_goals=campaign_goals,
        target_audience=target_audience,
        budget=budget,
        channels=channels,
        research_sources=research_sources,
        competitor_urls=competitor_urls,
        tone=tone,
        brand_voice_id=brand_voice_id,
        design_templates=answers.get("design_templates", []),
        schedule_time=None,  # Immediate deployment
        tenant_id=wizard_session.get("tenant_id", "default"),
        user_id=wizard_session.get("user_id", "system"),
        metadata={
            "wizard_id": wizard_session.get("wizard_id"),
            "wizard_session_id": wizard_session.get("session_id"),
            "reviewers": answers.get("reviewers", []),
        },
    )
    
    # Generate workflow ID
    campaign_id = f"campaign-{campaign_name.lower().replace(' ', '-')}-{int(datetime.utcnow().timestamp())}"
    workflow_id = campaign_id
    
    # Start workflow
    handle = await temporal_client.start_workflow(
        "MarketingCampaignWorkflow",
        campaign_input,
        id=workflow_id,
        task_queue=task_queue,
        start_timeout=timedelta(seconds=10),
        run_timeout=timedelta(hours=2),  # Max 2 hours (includes approval wait)
    )
    
    return {
        "workflow_id": handle.id,
        "run_id": handle.run_id,
        "campaign_id": campaign_id,
        "task_queue": task_queue,
        "started_at": datetime.utcnow().isoformat(),
    }


async def query_campaign_progress(
    temporal_client: temporal_client.Client,
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Query real-time campaign progress.
    
    Args:
        temporal_client: Temporal client instance
        workflow_id: Campaign workflow ID
        
    Returns:
        {
            "progress_percentage": 65,
            "current_phase": "design",
            "elapsed_seconds": 480
        }
    """
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # Query workflow for progress
    progress = await handle.query("get_progress")
    
    return progress


async def send_campaign_approval(
    temporal_client: temporal_client.Client,
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Send approval signal to campaign workflow.
    
    Args:
        temporal_client: Temporal client instance
        workflow_id: Campaign workflow ID
        
    Returns:
        {"status": "approved", "signal_sent_at": "..."}
    """
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # Send approval signal
    await handle.signal("approve_campaign")
    
    return {
        "status": "approved",
        "signal_sent_at": datetime.utcnow().isoformat(),
    }


async def update_campaign_content(
    temporal_client: temporal_client.Client,
    workflow_id: str,
    content_id: str,
    new_content: str,
) -> Dict[str, Any]:
    """
    Update campaign content during review phase.
    
    Args:
        temporal_client: Temporal client instance
        workflow_id: Campaign workflow ID
        content_id: Content identifier (e.g., "email_subject")
        new_content: Updated content
        
    Returns:
        {"status": "updated"}
    """
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # Send content update signal
    await handle.signal("update_content", content_id, new_content)
    
    return {
        "status": "updated",
        "content_id": content_id,
        "updated_at": datetime.utcnow().isoformat(),
    }


async def get_campaign_result(
    temporal_client: temporal_client.Client,
    workflow_id: str,
) -> Dict[str, Any]:
    """
    Get final campaign result (blocks until complete).
    
    Args:
        temporal_client: Temporal client instance
        workflow_id: Campaign workflow ID
        
    Returns:
        CampaignResult dict
    """
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # Wait for workflow completion
    result = await handle.result()
    
    return {
        "campaign_id": result.campaign_id,
        "status": result.status,
        "duration_seconds": result.duration_seconds,
        "analytics_dashboard_url": result.analytics_dashboard_url,
        "published_channels": result.distribution_results.get("published_channels", []),
    }
