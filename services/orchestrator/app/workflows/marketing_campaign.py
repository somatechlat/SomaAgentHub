"""
Marketing Campaign Workflow - Production-Ready Implementation.

Orchestrates end-to-end marketing campaign execution with:
- Saga pattern for automatic compensation
- Circuit breakers for external service protection
- Parallel execution with dependency management
- Real-time progress tracking
- Human-in-the-loop approval gates
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow

from ..patterns.saga import Saga
from .marketing_activities import (
    AnalyticsSetupInput,
    ContentCreationInput,
    DesignAssetsInput,
    DistributionInput,
    ResearchInput,
    ReviewApprovalInput,
    analytics_setup_activity,
    content_creation_activity,
    design_assets_activity,
    distribute_campaign_activity,
    research_phase_activity,
    review_approval_activity,
    # Compensation activities
    cleanup_analytics_activity,
    delete_content_drafts_activity,
    delete_design_assets_activity,
    rollback_distribution_activity,
)


@dataclass
class CampaignInput:
    """Input for marketing campaign workflow."""
    
    campaign_name: str
    campaign_goals: List[str]
    target_audience: str
    budget: float
    
    # Channel selection
    channels: List[str]  # ["email", "social", "blog"]
    
    # Research parameters
    research_sources: List[str]
    competitor_urls: List[str]
    
    # Content parameters
    tone: str  # "professional", "casual", "technical"
    brand_voice_id: Optional[str] = None
    
    # Design parameters
    design_templates: List[str] = field(default_factory=list)
    
    # Distribution parameters
    schedule_time: Optional[datetime] = None
    
    # Metadata
    tenant_id: str = "default"
    user_id: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignResult:
    """Result from marketing campaign workflow."""
    
    campaign_id: str
    status: str  # "success", "rejected", "failed"
    
    # Phase results
    research_results: Dict[str, Any]
    content: Dict[str, Any]
    design_assets: Dict[str, Any]
    distribution_results: Dict[str, Any]
    analytics_dashboard_url: str
    
    # Metadata
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    
    # Metrics
    total_activities: int
    failed_activities: int
    compensated_activities: int


@workflow.defn
class MarketingCampaignWorkflow:
    """
    End-to-end marketing campaign automation workflow.
    
    Features:
    - ✅ Automatic compensation (Saga pattern)
    - ✅ Circuit breakers for external services
    - ✅ Parallel execution where possible
    - ✅ Real-time progress tracking (signals/queries)
    - ✅ Human approval gates
    - ✅ Conditional distribution based on channels
    - ✅ Complete observability (logs, metrics, traces)
    
    Workflow Steps:
    1. Research Phase (2-3 min) - Parallel market research & competitor analysis
    2. Content Creation (5-10 min) - LLM-powered content generation
    3. Design Assets (3-5 min) - Parallel asset generation (Figma)
    4. Review & Approval (wait for human) - Human-in-the-loop quality gate
    5. Distribution (2-5 min) - Multi-channel parallel distribution
    6. Analytics Setup (1 min) - Metrics/logs wiring (Prometheus + Loki)
    
    Total Duration: 13-24 minutes (excluding approval wait)
    """
    
    def __init__(self):
        """Initialize workflow state."""
        self.progress_percentage = 0
        self.current_phase = "initializing"
        self.started_at: Optional[datetime] = None
        self.content_updates: Dict[str, str] = {}
        self.approval_received = False
    
    @workflow.signal
    def update_content(self, content_id: str, new_content: str) -> None:
        """
        Signal to update content during review phase.
        
        Allows human reviewers to modify content before distribution.
        """
        workflow.logger.info(
            f"Content update received for {content_id}",
            extra={"content_id": content_id, "length": len(new_content)},
        )
        self.content_updates[content_id] = new_content
    
    @workflow.signal
    def approve_campaign(self) -> None:
        """
        Signal to approve campaign for distribution.
        
        Triggers distribution phase after human review.
        """
        workflow.logger.info("Campaign approval received")
        self.approval_received = True
    
    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """
        Query current workflow progress.
        
        Returns real-time status for UI dashboards.
        """
        return {
            "progress_percentage": self.progress_percentage,
            "current_phase": self.current_phase,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "elapsed_seconds": (
                (workflow.now() - self.started_at).seconds
                if self.started_at
                else 0
            ),
            "content_updates": len(self.content_updates),
            "approval_received": self.approval_received,
        }
    
    @workflow.run
    async def run(self, input: CampaignInput) -> CampaignResult:
        """
        Execute complete marketing campaign workflow.
        
        Returns:
            Campaign execution results with all artifacts
        """
        self.started_at = workflow.now()
        campaign_id = f"campaign-{input.campaign_name}-{self.started_at.timestamp()}"
        
        workflow.logger.info(
            f"Starting marketing campaign: {input.campaign_name}",
            extra={
                "campaign_id": campaign_id,
                "channels": input.channels,
                "budget": input.budget,
            },
        )
        
        # Initialize saga for compensation tracking
        saga = Saga(campaign_id)
        
        try:
            # Phase 1: Research (parallel) - 20% progress
            self.current_phase = "research"
            research_results = await self._research_phase(saga, input)
            self.progress_percentage = 20
            
            # Phase 2: Content Creation (sequential) - 40% progress
            self.current_phase = "content_creation"
            content = await self._content_phase(saga, input, research_results)
            self.progress_percentage = 40
            
            # Phase 3: Design Assets (parallel) - 60% progress
            self.current_phase = "design"
            design_assets = await self._design_phase(saga, input, content)
            self.progress_percentage = 60
            
            # Phase 4: Review & Approval (human-in-the-loop) - 70% progress
            self.current_phase = "review"
            approved = await self._review_phase(input, content, design_assets)
            
            if not approved:
                # Campaign rejected - compensate all steps
                workflow.logger.warning("Campaign rejected by reviewer")
                await saga.compensate(reason="campaign_rejected")
                
                return CampaignResult(
                    campaign_id=campaign_id,
                    status="rejected",
                    research_results=research_results,
                    content=content,
                    design_assets=design_assets,
                    distribution_results={},
                    analytics_dashboard_url="",
                    started_at=self.started_at,
                    completed_at=workflow.now(),
                    duration_seconds=(workflow.now() - self.started_at).seconds,
                    total_activities=len(saga.executed),
                    failed_activities=0,
                    compensated_activities=len(saga.executed),
                )
            
            self.progress_percentage = 70
            
            # Phase 5: Distribution (parallel by channel) - 90% progress
            self.current_phase = "distribution"
            distribution_results = await self._distribution_phase(
                saga,
                input,
                content,
                design_assets,
            )
            self.progress_percentage = 90
            
            # Phase 6: Analytics Setup - 100% progress
            self.current_phase = "analytics"
            analytics_dashboard = await self._analytics_phase(saga, input, campaign_id)
            self.progress_percentage = 100
            
            self.current_phase = "completed"
            
            workflow.logger.info(
                f"Campaign {campaign_id} completed successfully",
                extra={
                    "duration_seconds": (workflow.now() - self.started_at).seconds,
                    "total_activities": len(saga.executed),
                },
            )
            
            return CampaignResult(
                campaign_id=campaign_id,
                status="success",
                research_results=research_results,
                content=content,
                design_assets=design_assets,
                distribution_results=distribution_results,
                analytics_dashboard_url=analytics_dashboard["dashboard_url"],
                started_at=self.started_at,
                completed_at=workflow.now(),
                duration_seconds=(workflow.now() - self.started_at).seconds,
                total_activities=len(saga.executed),
                failed_activities=0,
                compensated_activities=0,
            )
            
        except Exception as e:
            # Workflow failed - compensate all executed steps
            workflow.logger.error(
                f"Campaign {campaign_id} failed: {e}",
                extra={"error": str(e), "phase": self.current_phase},
            )
            
            await saga.compensate(reason=f"workflow_failure: {str(e)}")
            
            # Re-raise to mark workflow as failed
            raise
    
    async def _research_phase(
        self,
        saga: Saga,
        input: CampaignInput,
    ) -> Dict[str, Any]:
        """
        Phase 1: Market research and competitor analysis.
        
        Executes in parallel:
        - Market research (Notion search)
        - Competitor analysis (Playwright scraping)
        
        Duration: 2-3 minutes
        """
        workflow.logger.info("Starting research phase")
        
        research_input = ResearchInput(
            campaign_name=input.campaign_name,
            research_sources=input.research_sources,
            competitor_urls=input.competitor_urls,
            target_audience=input.target_audience,
        )
        
        # Execute with saga tracking and compensation
        result = await saga.execute(
            research_phase_activity,
            {"input": research_input},
            compensation=None,  # Research is read-only, no compensation needed
            timeout=timedelta(minutes=5),
        )
        
        workflow.logger.info(
            "Research phase completed",
            extra={"findings": len(result.get("findings", []))},
        )
        
        return result
    
    async def _content_phase(
        self,
        saga: Saga,
        input: CampaignInput,
        research_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 2: Content creation with LLM.
        
        Sequential steps:
        1. Retrieve brand voice from Memory Gateway
        2. Generate content with SLM
        3. Store content in Memory Gateway
        
        Duration: 5-10 minutes
        """
        workflow.logger.info("Starting content creation phase")
        
        content_input = ContentCreationInput(
            campaign_name=input.campaign_name,
            campaign_goals=input.campaign_goals,
            research_findings=research_results.get("findings", []),
            tone=input.tone,
            brand_voice_id=input.brand_voice_id,
            channels=input.channels,
        )
        
        # Execute with compensation (delete drafts on failure)
        result = await saga.execute(
            content_creation_activity,
            {"input": content_input},
            compensation=delete_content_drafts_activity,
            timeout=timedelta(minutes=15),
        )
        
        workflow.logger.info(
            "Content creation completed",
            extra={"content_pieces": len(result.get("content_pieces", []))},
        )
        
        return result
    
    async def _design_phase(
        self,
        saga: Saga,
        input: CampaignInput,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 3: Design asset generation.
        
        Parallel generation of:
        - Social media images
        - Email banners
        - Blog post images
        
        Duration: 3-5 minutes
        """
        workflow.logger.info("Starting design phase")
        
        design_input = DesignAssetsInput(
            campaign_name=input.campaign_name,
            content_headlines=content.get("headlines", []),
            templates=input.design_templates,
            channels=input.channels,
        )
        
        # Execute with compensation (delete Figma files on failure)
        result = await saga.execute(
            design_assets_activity,
            {"input": design_input},
            compensation=delete_design_assets_activity,
            timeout=timedelta(minutes=10),
        )
        
        workflow.logger.info(
            "Design phase completed",
            extra={"assets_created": len(result.get("assets", []))},
        )
        
        return result
    
    async def _review_phase(
        self,
        input: CampaignInput,
        content: Dict[str, Any],
        design_assets: Dict[str, Any],
    ) -> bool:
        """
        Phase 4: Human review and approval.
        
        Human-in-the-loop workflow:
        1. Create GitHub PR with content & assets
        2. Send Slack notification to reviewers
        3. Wait for approval signal (with timeout)
        
        Duration: Variable (wait for human)
        """
        workflow.logger.info("Starting review phase")
        
        review_input = ReviewApprovalInput(
            campaign_name=input.campaign_name,
            content=content,
            design_assets=design_assets,
            reviewers=input.metadata.get("reviewers", []),
        )
        
        # Create review artifacts (GitHub PR, Slack message)
        await workflow.execute_activity(
            review_approval_activity,
            {"input": review_input},
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        # Wait for approval signal (with 24h timeout)
        workflow.logger.info("Waiting for campaign approval...")
        
        try:
            await workflow.wait_condition(
                lambda: self.approval_received,
                timeout=timedelta(hours=24),
            )
            
            workflow.logger.info("Campaign approved")
            return True
            
        except asyncio.TimeoutError:
            workflow.logger.warning("Approval timeout (24h) - rejecting campaign")
            return False
    
    async def _distribution_phase(
        self,
        saga: Saga,
        input: CampaignInput,
        content: Dict[str, Any],
        design_assets: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 5: Multi-channel distribution.
        
        Conditional parallel distribution based on selected channels:
        - Email: SendGrid/Mailchimp
        - Social: Buffer/LinkedIn/Twitter
        - Blog: GitHub Pages/WordPress
        
        Duration: 2-5 minutes
        """
        workflow.logger.info(
            "Starting distribution phase",
            extra={"channels": input.channels},
        )
        
        # Apply content updates from review
        if self.content_updates:
            workflow.logger.info(
                f"Applying {len(self.content_updates)} content updates",
            )
            for content_id, new_content in self.content_updates.items():
                content[content_id] = new_content
        
        distribution_input = DistributionInput(
            campaign_name=input.campaign_name,
            channels=input.channels,
            content=content,
            design_assets=design_assets,
            schedule_time=input.schedule_time,
        )
        
        # Execute with compensation (rollback published content)
        result = await saga.execute(
            distribute_campaign_activity,
            {"input": distribution_input},
            compensation=rollback_distribution_activity,
            timeout=timedelta(minutes=10),
        )
        
        workflow.logger.info(
            "Distribution completed",
            extra={
                "channels_published": len(result.get("published_channels", [])),
            },
        )
        
        return result
    
    async def _analytics_phase(
        self,
        saga: Saga,
        input: CampaignInput,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """
    Phase 6: Analytics setup.

    Emits metrics and returns analytics hints suitable for Prometheus+Loki based monitoring.
        
        Duration: 1 minute
        """
        workflow.logger.info("Starting analytics setup")
        
        analytics_input = AnalyticsSetupInput(
            campaign_id=campaign_id,
            campaign_name=input.campaign_name,
            channels=input.channels,
            metrics=["views", "clicks", "conversions", "revenue"],
        )
        
        # Execute with compensation (delete dashboard on failure)
        result = await saga.execute(
            analytics_setup_activity,
            {"input": analytics_input},
            compensation=cleanup_analytics_activity,
            timeout=timedelta(minutes=2),
        )
        
        workflow.logger.info(
            "Analytics setup completed",
            extra={"dashboard_url": result.get("dashboard_url")},
        )
        
        return result
