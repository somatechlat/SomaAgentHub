"""Analytics service client for SomaGent platform.

Provides access to historical metrics, usage trends, and cost forecasting.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class AnalyticsClient:
    """Client for analytics service API."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        api_key: Optional[str] = None,
    ):
        """Initialize analytics client.
        
        Args:
            base_url: Analytics service base URL
            timeout: Request timeout in seconds
            api_key: API key for authentication (optional)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

    async def query_metrics(
        self,
        metric_name: str,
        tenant_id: Optional[str] = None,
        time_range_days: int = 30,
        aggregation: str = "avg",
        group_by: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Query historical metrics from ClickHouse.
        
        Args:
            metric_name: Metric to query (e.g., "slm.tokens", "slm.cost")
            tenant_id: Filter by tenant (optional)
            time_range_days: Number of days to look back
            aggregation: Aggregation function (avg, sum, count, max, min)
            group_by: Fields to group by (e.g., ["model", "tenant_id"])
            
        Returns:
            Dictionary with query results
        """
        url = f"{self.base_url}/v1/metrics/query"
        
        params = {
            "metric": metric_name,
            "time_range_days": time_range_days,
            "aggregation": aggregation,
        }
        
        if tenant_id:
            params["tenant_id"] = tenant_id
        
        if group_by:
            params["group_by"] = ",".join(group_by)
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Analytics query timed out: {metric_name}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Analytics query failed: {exc.response.status_code}"
            ) from exc

    async def get_token_usage(
        self,
        tenant_id: str,
        model: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get token usage statistics for a tenant.
        
        Returns:
            Dictionary with usage stats:
                - total_tokens: Total tokens used
                - avg_prompt_tokens: Average prompt tokens per request
                - avg_completion_tokens: Average completion tokens per request
                - request_count: Total number of requests
                - by_model: Breakdown by model
        """
        filters = {}
        if model:
            filters["model"] = model
        
        result = await self.query_metrics(
            metric_name="slm.tokens",
            tenant_id=tenant_id,
            time_range_days=days,
            aggregation="sum",
            group_by=["model"] if not model else None,
        )
        
        return result

    async def get_cost_analysis(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get cost analysis for a tenant.
        
        Returns:
            Dictionary with cost stats:
                - total_cost_usd: Total cost
                - avg_cost_per_request: Average cost per request
                - by_model: Cost breakdown by model
                - daily_trend: Cost by day
        """
        result = await self.query_metrics(
            metric_name="slm.cost",
            tenant_id=tenant_id,
            time_range_days=days,
            aggregation="sum",
            group_by=["model", "date"],
        )
        
        return result

    async def forecast_cost(
        self,
        tenant_id: str,
        forecast_days: int = 30,
        historical_days: int = 90,
    ) -> Dict[str, Any]:
        """Forecast future costs based on historical trends.
        
        Args:
            tenant_id: Tenant ID
            forecast_days: Number of days to forecast
            historical_days: Number of historical days to analyze
            
        Returns:
            Dictionary with forecast:
                - forecasted_cost_usd: Predicted cost
                - confidence_interval: [low, high] bounds
                - trend: "increasing", "stable", "decreasing"
        """
        url = f"{self.base_url}/v1/analytics/forecast"
        
        params = {
            "tenant_id": tenant_id,
            "forecast_days": forecast_days,
            "historical_days": historical_days,
            "metric": "cost",
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as exc:
            raise RuntimeError("Cost forecast timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Cost forecast failed: {exc.response.status_code}"
            ) from exc

    async def get_model_recommendations(
        self,
        tenant_id: str,
        task_type: str = "general",
    ) -> List[Dict[str, Any]]:
        """Get model recommendations based on usage patterns.
        
        Args:
            tenant_id: Tenant ID
            task_type: Type of task ("general", "coding", "creative", etc.)
            
        Returns:
            List of recommended models with cost savings estimates
        """
        url = f"{self.base_url}/v1/analytics/recommendations"
        
        params = {
            "tenant_id": tenant_id,
            "task_type": task_type,
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as exc:
            raise RuntimeError("Recommendations request timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Recommendations request failed: {exc.response.status_code}"
            ) from exc

    async def health_check(self) -> bool:
        """Check if analytics service is accessible."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


def get_analytics_client() -> AnalyticsClient:
    """Get analytics client from environment variables.
    
    Required environment variables:
        ANALYTICS_SERVICE_URL: Analytics service base URL
        ANALYTICS_API_KEY: API key (optional)
        ANALYTICS_TIMEOUT: Request timeout in seconds (optional, default: 10.0)
    """
    url = os.getenv("ANALYTICS_SERVICE_URL")
    if not url:
        raise RuntimeError("ANALYTICS_SERVICE_URL environment variable not set")
    
    api_key = os.getenv("ANALYTICS_API_KEY")
    timeout = float(os.getenv("ANALYTICS_TIMEOUT", "10.0"))
    
    return AnalyticsClient(
        base_url=url,
        timeout=timeout,
        api_key=api_key,
    )
