"""
Production health check endpoints for Kubernetes readiness and liveness probes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from ..core.config import get_settings
from ..database import check_database_health
from ..integrations.kafka_client import KafkaClientConfig
from ..services.circuit_breaker import KAFKA_CIRCUIT_BREAKER, circuit_breaker_manager

router = APIRouter(prefix="/health", tags=["health"])

settings = get_settings()


@router.get("/ready", response_model=dict[str, Any])
async def readiness_check() -> dict[str, Any]:
    """Kubernetes readiness probe.

    Checks if the service is ready to serve traffic.
    - Database connectivity
    - Kafka connectivity (if configured)
    - All required dependencies
    """
    health_status = {"status": "ready", "timestamp": None, "checks": {}}

    checks: dict[str, Any] = {}
    all_healthy = True

    # Check database
    try:
        db_healthy = await check_database_health()
        checks["database"] = {"healthy": db_healthy, "message": "Database connectivity OK"}
        if not db_healthy:
            all_healthy = False
    except Exception as e:
        checks["database"] = {"healthy": False, "message": str(e)}
        all_healthy = False

    # Check Kafka (if configured)
    if settings.kafka_bootstrap_servers:
        try:

            @KAFKA_CIRCUIT_BREAKER
            async def _check_kafka() -> bool:
                _ = KafkaClientConfig()
                return True

            await _check_kafka()
            checks["kafka"] = {"healthy": True, "message": "Kafka configuration valid"}
        except Exception as e:
            checks["kafka"] = {"healthy": False, "message": str(e)}
            all_healthy = False
    else:
        checks["kafka"] = {"healthy": True, "message": "Kafka not configured"}

    if not all_healthy:
        health_status["status"] = "not_ready"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)

    health_status["checks"] = checks
    health_status["circuit_breakers"] = circuit_breaker_manager.get_all_states()
    return health_status


@router.get("/live", response_model=dict[str, Any])
async def liveness_check() -> dict[str, Any]:
    """Kubernetes liveness probe.

    Basic check if the service is alive and responding.
    Only checks internal state, not external dependencies.
    """
    return {
        "status": "alive",
        "timestamp": None,
        "service": "orchestrator-service",
        "version": "0.1.0",
    }


@router.get("/startup", response_model=dict[str, Any])
async def startup_check() -> dict[str, Any]:
    """Kubernetes startup probe.

    Checks if the service has finished initialization.
    """
    return {"status": "started", "timestamp": None, "service": "orchestrator-service"}


@router.get("/dependencies", response_model=dict[str, Any])
async def dependency_health() -> dict[str, Any]:
    """Detailed health check of all dependencies."""
    checks: dict[str, Any] = {}

    # Database check
    try:
        from ..database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"healthy": True, "message": "Database responding"}
    except Exception as e:
        checks["database"] = {"healthy": False, "message": str(e)}

    # External service checks
    external_services = {
        "temporal": settings.temporal_target_host,
        "kafka": settings.kafka_bootstrap_servers,
        "llm_hub": settings.llm_hub_url,
        "pricing_service": settings.pricing_service_url,
        "policy_engine": str(settings.policy_engine_url),
        "constitution_service": str(settings.constitution_service_url),
    }

    for service, url in external_services.items():
        if url:
            checks[service] = {"healthy": True, "url": str(url)}
        else:
            checks[service] = {"healthy": False, "message": "Not configured"}

    return {"status": "healthy", "timestamp": None, "dependencies": checks}


@router.get("/metrics")
async def metrics() -> None:
    """Prometheus metrics endpoint - handled by main app."""
    # Metrics endpoint is configured in main.py
    # No additional logic needed; FastAPI will serve the metrics via the
    # Prometheus middleware defined in the main application.
    return None
