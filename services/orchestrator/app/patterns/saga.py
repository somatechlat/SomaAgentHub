"""
Saga Pattern Implementation for Temporal Workflows.

Provides automatic compensation (rollback) logic for distributed transactions.
Inspired by microservices patterns from Netflix, Uber, and Stripe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from temporalio import workflow


@dataclass
class CompensationPair:
    """
    Tracks a forward operation and its compensation.
    
    Example:
        CompensationPair(
            forward="create_github_repo",
            forward_result={"repo_id": "123", "name": "campaign-assets"},
            backward=delete_github_repo_activity,
            backward_args={"repo_id": "123"}
        )
    """
    forward: str  # Name of forward activity
    forward_result: Any  # Result from forward execution
    backward: Callable  # Compensation activity function
    backward_args: Dict[str, Any]  # Args for compensation


class Saga:
    """
    Saga orchestrator for distributed transactions.
    
    Automatically tracks all executed activities and their compensations.
    On failure, executes compensations in reverse order to maintain consistency.
    
    Usage:
        saga = Saga("campaign_setup")
        
        try:
            # Execute activities with compensation tracking
            repo = await saga.execute(
                create_github_repo_activity,
                {"name": "campaign-repo", "private": True},
                compensation=delete_github_repo_activity,
            )
            
            channel = await saga.execute(
                create_slack_channel_activity,
                {"name": "campaign-team"},
                compensation=archive_slack_channel_activity,
            )
            
            page = await saga.execute(
                create_notion_page_activity,
                {"title": "Campaign Brief"},
                compensation=delete_notion_page_activity,
            )
            
        except Exception:
            # Automatic rollback of all 3 operations
            await saga.compensate()
            raise
    
    Real-World Benefits:
    - No orphaned resources on failure
    - Automatic cleanup
    - Idempotent rollback (safe to retry)
    - Complete audit trail via Temporal history
    """
    
    def __init__(self, saga_id: str):
        """
        Initialize saga with unique identifier.
        
        Args:
            saga_id: Unique identifier for this saga (e.g., "campaign_setup_123")
        """
        self.saga_id = saga_id
        self.executed: List[CompensationPair] = []
        self.compensated = False
    
    async def execute(
        self,
        activity: Callable,
        args: Dict[str, Any],
        compensation: Optional[Callable] = None,
        compensation_args: Optional[Dict[str, Any]] = None,
        timeout: timedelta = timedelta(seconds=30),
        retry_policy: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute activity with compensation tracking.
        
        Args:
            activity: Temporal activity function to execute
            args: Arguments for the activity
            compensation: Optional compensation activity (for rollback)
            compensation_args: Optional args for compensation (auto-extracted if None)
            timeout: Activity execution timeout
            retry_policy: Custom retry policy for this activity
            
        Returns:
            Activity execution result
            
        Raises:
            Exception: If activity fails (after retries)
        """
        workflow.logger.info(
            f"[Saga:{self.saga_id}] Executing {activity.__name__}",
            extra={"activity": activity.__name__, "args": args},
        )
        
        try:
            # Execute activity with Temporal retry logic
            result = await workflow.execute_activity(
                activity,
                args,
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            
            # Track compensation if provided
            if compensation:
                # Auto-extract compensation args from result if not provided
                if compensation_args is None:
                    compensation_args = self._extract_compensation_args(result, args)
                
                self.executed.append(
                    CompensationPair(
                        forward=activity.__name__,
                        forward_result=result,
                        backward=compensation,
                        backward_args=compensation_args,
                    )
                )
                
                workflow.logger.info(
                    f"[Saga:{self.saga_id}] Tracked compensation for {activity.__name__}",
                    extra={
                        "compensation": compensation.__name__,
                        "total_tracked": len(self.executed),
                    },
                )
            
            return result
            
        except Exception as e:
            workflow.logger.error(
                f"[Saga:{self.saga_id}] Activity {activity.__name__} failed: {e}",
                extra={
                    "activity": activity.__name__,
                    "error": str(e),
                    "executed_steps": len(self.executed),
                },
            )
            raise
    
    async def compensate(self, reason: str = "rollback") -> None:
        """
        Execute all compensations in reverse order.
        
        Called automatically on saga failure, or manually for explicit rollback.
        Compensations execute in reverse order to maintain referential integrity.
        
        Args:
            reason: Reason for compensation (for logging/audit)
            
        Example:
            Step 1: Create GitHub repo → ID: 123
            Step 2: Create Slack channel → repo_id: 123
            Step 3: Create Notion page → repo_id: 123
            
            Compensation order (reverse):
            Step 3: Delete Notion page
            Step 2: Archive Slack channel
            Step 1: Delete GitHub repo
        """
        if self.compensated:
            workflow.logger.warning(
                f"[Saga:{self.saga_id}] Already compensated, skipping",
            )
            return
        
        workflow.logger.warning(
            f"[Saga:{self.saga_id}] Starting compensation: {reason}",
            extra={
                "reason": reason,
                "steps_to_compensate": len(self.executed),
            },
        )
        
        # Execute compensations in reverse order
        for i, pair in enumerate(reversed(self.executed), 1):
            try:
                workflow.logger.info(
                    f"[Saga:{self.saga_id}] Compensating {pair.forward} "
                    f"({i}/{len(self.executed)})",
                    extra={
                        "forward_activity": pair.forward,
                        "compensation_activity": pair.backward.__name__,
                    },
                )
                
                # Execute compensation activity
                await workflow.execute_activity(
                    pair.backward,
                    pair.backward_args,
                    start_to_close_timeout=timedelta(seconds=30),
                    # No retries for compensations - fail fast
                    retry_policy={"maximum_attempts": 1},
                )
                
                workflow.logger.info(
                    f"[Saga:{self.saga_id}] Compensated {pair.forward}",
                )
                
            except Exception as comp_error:
                # Log but continue compensating (best effort)
                workflow.logger.error(
                    f"[Saga:{self.saga_id}] Compensation failed for {pair.forward}",
                    extra={
                        "forward_activity": pair.forward,
                        "compensation_activity": pair.backward.__name__,
                        "error": str(comp_error),
                    },
                )
                # Continue compensating remaining steps
        
        self.compensated = True
        
        workflow.logger.warning(
            f"[Saga:{self.saga_id}] Compensation complete",
            extra={
                "total_compensated": len(self.executed),
                "reason": reason,
            },
        )
    
    def _extract_compensation_args(
        self,
        result: Any,
        forward_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract compensation arguments from activity result.
        
        Convention:
        - If result is dict with "id" field: {"id": result["id"]}
        - If result is dict with "{resource}_id": use that
        - Otherwise: use original forward args
        
        Examples:
            result = {"repo_id": "123"} → {"repo_id": "123"}
            result = {"id": "abc"} → {"id": "abc"}
            result = "simple_string" → forward_args
        """
        if isinstance(result, dict):
            # Look for common ID patterns
            if "id" in result:
                return {"id": result["id"]}
            
            # Look for {resource}_id pattern
            for key, value in result.items():
                if key.endswith("_id"):
                    return {key: value}
            
            # Use entire result
            return result
        
        # Fallback: use original args
        return forward_args


class SagaBuilder:
    """
    Fluent builder for creating sagas with pre-configured steps.
    
    Usage:
        saga = (
            SagaBuilder("campaign_setup")
            .add_step(
                create_github_repo_activity,
                {"name": "repo"},
                compensation=delete_github_repo_activity,
            )
            .add_step(
                create_slack_channel_activity,
                {"name": "channel"},
                compensation=archive_slack_channel_activity,
            )
            .build()
        )
        
        await saga.execute_all()
    """
    
    def __init__(self, saga_id: str):
        self.saga = Saga(saga_id)
        self.steps: List[Dict[str, Any]] = []
    
    def add_step(
        self,
        activity: Callable,
        args: Dict[str, Any],
        compensation: Optional[Callable] = None,
        **kwargs,
    ) -> SagaBuilder:
        """Add step to saga builder (fluent interface)."""
        self.steps.append({
            "activity": activity,
            "args": args,
            "compensation": compensation,
            **kwargs,
        })
        return self
    
    async def execute_all(self) -> List[Any]:
        """Execute all steps in order."""
        results = []
        
        try:
            for step in self.steps:
                result = await self.saga.execute(**step)
                results.append(result)
            
            return results
            
        except Exception:
            # Auto-compensate on failure
            await self.saga.compensate()
            raise
    
    def build(self) -> Saga:
        """Return configured saga (for manual execution)."""
        return self.saga
