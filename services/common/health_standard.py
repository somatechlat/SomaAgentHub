"""Standardized Health Check Module for SomaAgentHub SaaS Platform.

Provides consistent health check implementations across all services per Requirements 4.1-4.5.

Endpoints:
- /health: Simple liveness check returning {"status": "healthy|degraded|unhealthy", "service": "<name>"}
- /healthz: Detailed health with dependency checks
- /metrics: Prometheus-compatible metrics

Usage:
    from services.common.health_standard import create_health_router, HealthStatus

    # Create router with service name and optional dependency checks
    health_router = create_health_router(
        service_name="my-service",
        version="1.0.0",
        dependency_checks={
            "database": check_database,
            "redis": check_redis,
        }
    )
    app.include_router(health_router)
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum

from fastapi import APIRouter, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Standard health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyStatus(BaseModel):
    """Status of a single dependency."""

    status: HealthStatus
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Standard /health endpoint response.

    Per Requirement 4.2: SHALL return JSON with status and service fields.
    """

    status: HealthStatus = Field(..., description="Health status: healthy, degraded, or unhealthy")
    service: str = Field(..., description="Service name")
    version: str | None = Field(None, description="Service version")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class DetailedHealthResponse(BaseModel):
    """Standard /healthz endpoint response.

    Per Requirement 4.3: SHALL check all critical dependencies and return individual statuses.
    """

    status: HealthStatus = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str | None = Field(None, description="Service version")
    dependencies: dict[str, DependencyStatus] = Field(default_factory=dict, description="Status of each dependency")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# Prometheus metrics for health monitoring
HEALTH_CHECK_TOTAL = Counter(
    "health_check_total", "Total health check requests", labelnames=["service", "endpoint", "status"]
)

HEALTH_CHECK_LATENCY = Gauge(
    "health_check_latency_seconds", "Health check latency in seconds", labelnames=["service", "dependency"]
)

DEPENDENCY_UP = Gauge("dependency_up", "Dependency availability (1=up, 0=down)", labelnames=["service", "dependency"])


class HealthChecker:
    """Manages health checks for a service."""

    def __init__(
        self,
        service_name: str,
        version: str = "1.0.0",
        dependency_checks: dict[str, Callable] | None = None,
    ):
        """Initialize health checker.

        Args:
            service_name: Name of the service
            version: Service version
            dependency_checks: Dict of dependency name -> async check function
                              Each function should return True if healthy, False otherwise
        """
        self.service_name = service_name
        self.version = version
        self.dependency_checks = dependency_checks or {}
        self._is_ready = False

    def set_ready(self, ready: bool = True) -> None:
        """Mark service as ready to accept traffic."""
        self._is_ready = ready
        logger.info(f"Service {self.service_name} readiness set to: {ready}")

    async def check_dependency(self, name: str, check_func: Callable) -> DependencyStatus:
        """Check a single dependency with timeout and error handling."""
        start_time = asyncio.get_event_loop().time()

        try:
            # Run check with 5 second timeout
            is_healthy = await asyncio.wait_for(check_func(), timeout=5.0)
            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

            # Update Prometheus metrics
            HEALTH_CHECK_LATENCY.labels(service=self.service_name, dependency=name).set(latency / 1000)
            DEPENDENCY_UP.labels(service=self.service_name, dependency=name).set(1 if is_healthy else 0)

            return DependencyStatus(status=status, latency_ms=latency)

        except TimeoutError:
            DEPENDENCY_UP.labels(service=self.service_name, dependency=name).set(0)
            return DependencyStatus(status=HealthStatus.UNHEALTHY, error="Timeout after 5 seconds")
        except Exception as e:
            DEPENDENCY_UP.labels(service=self.service_name, dependency=name).set(0)
            logger.warning(f"Dependency check failed for {name}: {e}")
            return DependencyStatus(status=HealthStatus.UNHEALTHY, error=str(e))

    async def get_health(self) -> HealthResponse:
        """Get simple health status (liveness check)."""
        # Simple liveness - if we can respond, we're alive
        status = HealthStatus.HEALTHY

        HEALTH_CHECK_TOTAL.labels(service=self.service_name, endpoint="/health", status=status.value).inc()

        return HealthResponse(
            status=status,
            service=self.service_name,
            version=self.version,
        )

    async def get_detailed_health(self) -> DetailedHealthResponse:
        """Get detailed health with dependency checks (readiness check)."""
        dependencies = {}

        # Check all dependencies concurrently
        if self.dependency_checks:
            tasks = {
                name: self.check_dependency(name, check_func) for name, check_func in self.dependency_checks.items()
            }

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            for name, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    dependencies[name] = DependencyStatus(status=HealthStatus.UNHEALTHY, error=str(result))
                else:
                    dependencies[name] = result

        # Determine overall status
        if not dependencies:
            overall_status = HealthStatus.HEALTHY
        elif all(d.status == HealthStatus.HEALTHY for d in dependencies.values()):
            overall_status = HealthStatus.HEALTHY
        elif any(d.status == HealthStatus.HEALTHY for d in dependencies.values()):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY

        HEALTH_CHECK_TOTAL.labels(service=self.service_name, endpoint="/healthz", status=overall_status.value).inc()

        return DetailedHealthResponse(
            status=overall_status,
            service=self.service_name,
            version=self.version,
            dependencies=dependencies,
        )


def create_health_router(
    service_name: str,
    version: str = "1.0.0",
    dependency_checks: dict[str, Callable] | None = None,
) -> APIRouter:
    """Create a standardized health check router for a service.

    Args:
        service_name: Name of the service
        version: Service version
        dependency_checks: Dict of dependency name -> async check function

    Returns:
        FastAPI APIRouter with /health, /healthz, and /metrics endpoints
    """
    router = APIRouter(tags=["health"])
    checker = HealthChecker(
        service_name=service_name,
        version=version,
        dependency_checks=dependency_checks,
    )

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Simple liveness check.

        Per Requirement 4.1: SHALL provide /health endpoint.
        Per Requirement 4.2: SHALL return JSON with status and service fields.
        """
        return await checker.get_health()

    @router.get("/healthz", response_model=DetailedHealthResponse)
    async def healthz(response: Response) -> DetailedHealthResponse:
        """Detailed health check with dependencies.

        Per Requirement 4.3: SHALL check all critical dependencies.
        Per Requirement 4.5: IF dependency checks fail, SHALL return HTTP 503.
        """
        result = await checker.get_detailed_health()

        if result.status == HealthStatus.UNHEALTHY:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return result

    @router.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint.

        Per Requirement 4.4: SHALL expose Prometheus-compatible metrics.
        """
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router


def get_health_checker(
    service_name: str,
    version: str = "1.0.0",
    dependency_checks: dict[str, Callable] | None = None,
) -> HealthChecker:
    """Get a HealthChecker instance for programmatic health checks."""
    return HealthChecker(
        service_name=service_name,
        version=version,
        dependency_checks=dependency_checks,
    )
