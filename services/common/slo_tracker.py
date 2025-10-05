"""
SLO (Service Level Objective) tracking and monitoring.

Tracks availability, latency, and error rate SLOs.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SLOStatus(str, Enum):
    """SLO status."""
    
    HEALTHY = "healthy"  # Meeting SLO target
    AT_RISK = "at_risk"  # Within 10% of target
    VIOLATED = "violated"  # Below SLO target


@dataclass
class SLO:
    """Service Level Objective definition."""
    
    name: str
    service: str
    metric: str  # availability, latency_p95, latency_p99, error_rate
    target: float  # Target percentage (e.g., 99.9 for 99.9%)
    window: str  # Time window: 1h, 24h, 7d, 30d
    description: str
    
    # Alerting thresholds
    warning_threshold: float = 0.9  # Alert at 90% of error budget
    critical_threshold: float = 1.0  # Alert at 100% of error budget


# SLO definitions for SomaAgent services
SERVICE_SLOS: List[SLO] = [
    # Gateway API
    SLO(
        name="gateway_availability",
        service="gateway-api",
        metric="availability",
        target=99.9,  # 99.9% uptime
        window="30d",
        description="Gateway API availability over 30 days"
    ),
    SLO(
        name="gateway_latency_p95",
        service="gateway-api",
        metric="latency_p95",
        target=200.0,  # 200ms p95 latency
        window="24h",
        description="Gateway API p95 latency under 200ms"
    ),
    SLO(
        name="gateway_error_rate",
        service="gateway-api",
        metric="error_rate",
        target=0.1,  # 0.1% error rate
        window="24h",
        description="Gateway API error rate below 0.1%"
    ),
    
    # SLM Service
    SLO(
        name="slm_availability",
        service="slm-service",
        metric="availability",
        target=99.5,  # 99.5% uptime
        window="30d",
        description="SLM service availability over 30 days"
    ),
    SLO(
        name="slm_latency_p99",
        service="slm-service",
        metric="latency_p99",
        target=2000.0,  # 2s p99 latency
        window="24h",
        description="SLM service p99 latency under 2s"
    ),
    
    # Memory Gateway
    SLO(
        name="memory_availability",
        service="memory-gateway",
        metric="availability",
        target=99.9,  # 99.9% uptime
        window="30d",
        description="Memory gateway availability over 30 days"
    ),
    SLO(
        name="memory_latency_p95",
        service="memory-gateway",
        metric="latency_p95",
        target=100.0,  # 100ms p95 latency
        window="24h",
        description="Memory gateway p95 latency under 100ms"
    ),
    
    # Constitution Service
    SLO(
        name="constitution_availability",
        service="constitution-service",
        metric="availability",
        target=99.95,  # 99.95% uptime (critical service)
        window="30d",
        description="Constitution service availability over 30 days"
    ),
]


class SLOTracker:
    """Track SLO compliance and error budgets."""
    
    def __init__(self, prometheus_url: str = "http://prometheus:9090"):
        """
        Initialize SLO tracker.
        
        Args:
            prometheus_url: Prometheus server URL
        """
        self.prometheus_url = prometheus_url
    
    def calculate_availability(
        self,
        service: str,
        window: str
    ) -> float:
        """
        Calculate service availability.
        
        Args:
            service: Service name
            window: Time window (1h, 24h, 7d, 30d)
            
        Returns:
            Availability percentage
        """
        # Query Prometheus for uptime
        query = f"""
            100 * (
                sum(rate(http_requests_total{{service="{service}",code!~"5.."}}[{window}]))
                /
                sum(rate(http_requests_total{{service="{service}"}}[{window}]))
            )
        """
        
        result = self._query_prometheus(query)
        if result:
            return float(result[0]["value"][1])
        
        return 100.0  # Default to 100% if no data
    
    def calculate_latency_percentile(
        self,
        service: str,
        percentile: int,
        window: str
    ) -> float:
        """
        Calculate latency percentile.
        
        Args:
            service: Service name
            percentile: Percentile (95, 99)
            window: Time window
            
        Returns:
            Latency in milliseconds
        """
        quantile = percentile / 100.0
        query = f"""
            histogram_quantile(
                {quantile},
                rate(http_request_duration_seconds_bucket{{service="{service}"}}[{window}])
            ) * 1000
        """
        
        result = self._query_prometheus(query)
        if result:
            return float(result[0]["value"][1])
        
        return 0.0
    
    def calculate_error_rate(
        self,
        service: str,
        window: str
    ) -> float:
        """
        Calculate error rate.
        
        Args:
            service: Service name
            window: Time window
            
        Returns:
            Error rate percentage
        """
        query = f"""
            100 * (
                sum(rate(http_requests_total{{service="{service}",code=~"5.."}}[{window}]))
                /
                sum(rate(http_requests_total{{service="{service}"}}[{window}]))
            )
        """
        
        result = self._query_prometheus(query)
        if result:
            return float(result[0]["value"][1])
        
        return 0.0
    
    def check_slo(self, slo: SLO) -> Dict:
        """
        Check if SLO is being met.
        
        Args:
            slo: SLO definition
            
        Returns:
            SLO status with current value and error budget
        """
        # Get current metric value
        if slo.metric == "availability":
            current = self.calculate_availability(slo.service, slo.window)
            is_met = current >= slo.target
            error_budget = 100.0 - slo.target  # Total allowed downtime
            error_budget_consumed = (100.0 - current) / error_budget if error_budget > 0 else 0
            
        elif slo.metric.startswith("latency_p"):
            percentile = int(slo.metric.split("_p")[1])
            current = self.calculate_latency_percentile(slo.service, percentile, slo.window)
            is_met = current <= slo.target
            error_budget = slo.target  # Max allowed latency
            error_budget_consumed = current / error_budget if error_budget > 0 else 0
            
        elif slo.metric == "error_rate":
            current = self.calculate_error_rate(slo.service, slo.window)
            is_met = current <= slo.target
            error_budget = slo.target  # Max allowed error rate
            error_budget_consumed = current / error_budget if error_budget > 0 else 0
        
        else:
            raise ValueError(f"Unknown metric: {slo.metric}")
        
        # Determine status
        if not is_met:
            status = SLOStatus.VIOLATED
        elif error_budget_consumed >= slo.warning_threshold:
            status = SLOStatus.AT_RISK
        else:
            status = SLOStatus.HEALTHY
        
        return {
            "slo": slo.name,
            "service": slo.service,
            "metric": slo.metric,
            "target": slo.target,
            "current": current,
            "is_met": is_met,
            "status": status.value,
            "error_budget_consumed": error_budget_consumed * 100,  # Percentage
            "window": slo.window,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def check_all_slos(self) -> List[Dict]:
        """
        Check all defined SLOs.
        
        Returns:
            List of SLO status reports
        """
        results = []
        for slo in SERVICE_SLOS:
            try:
                result = self.check_slo(slo)
                results.append(result)
                
                # Log violations
                if result["status"] == SLOStatus.VIOLATED.value:
                    logger.error(
                        f"SLO VIOLATED: {slo.name} - "
                        f"current={result['current']}, target={slo.target}"
                    )
                elif result["status"] == SLOStatus.AT_RISK.value:
                    logger.warning(
                        f"SLO AT RISK: {slo.name} - "
                        f"error budget {result['error_budget_consumed']:.1f}% consumed"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to check SLO {slo.name}: {e}")
                results.append({
                    "slo": slo.name,
                    "service": slo.service,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def _query_prometheus(self, query: str) -> Optional[List[Dict]]:
        """
        Query Prometheus.
        
        Args:
            query: PromQL query
            
        Returns:
            Query result
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            if data["status"] == "success":
                return data["data"]["result"]
            
            return None
            
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return None
