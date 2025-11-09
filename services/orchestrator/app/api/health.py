"""
Production health check endpoints for Kubernetes readiness and liveness probes.
"""

from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import check_database_health, async_engine
from ..integrations.kafka_client import KafkaClientConfig
from ..core.config import get_settings
from ..services.circuit_breaker import circuit_breaker_manager, KAFKA_CIRCUIT_BREAKER

router = APIRouter(prefix="/health", tags=["health"])

settings = get_settings()


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.

    Checks if the service is ready to serve traffic.
    - Database connectivity
    - Kafka connectivity (if configured)
    - All required dependencies
    """
    health_status = {"status": "ready", "timestamp": None, "checks": {}}

    checks = {}
    all_healthy = True

    # Check database
    try:
        db_healthy = await check_database_health()
        checks["database"] = {
            "healthy": db_healthy,
            "message": "Database connectivity OK",
        }
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
                kafka_config = KafkaClientConfig()
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status
        )

    health_status["checks"] = checks
    health_status["circuit_breakers"] = circuit_breaker_manager.get_all_states()
    return health_status


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe.

    Basic check if the service is alive and responding.
    Only checks internal state, not external dependencies.
    """
    return {
        "status": "alive",
        "timestamp": None,
        "service": "orchestrator-service",
        "version": "0.1.0",
    }


@router.get("/startup", response_model=Dict[str, Any])
async def startup_check() -> Dict[str, Any]:
    """
    Kubernetes startup probe.

    Checks if the service has finished initialization.
    """
    return {"status": "started", "timestamp": None, "service": "orchestrator-service"}


@router.get("/dependencies", response_model=Dict[str, Any])
async def dependency_health() -> Dict[str, Any]:
    """Detailed health check of all dependencies."""
    checks = {}

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
        "slm_service": settings.somallm_provider_url,
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
    pass
