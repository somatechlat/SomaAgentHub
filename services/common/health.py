"""
Health and readiness endpoints for Kubernetes probes.
Common implementation for all SomaAgent services.
"""

from fastapi import APIRouter, Response, status
from typing import Dict, Any, Callable, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthCheck:
    """
    Health check manager for service monitoring.
    
    Tracks service health status and dependencies.
    """
    
    def __init__(self):
        self.is_ready = False
        self.dependency_checks: Dict[str, Callable] = {}
    
    def set_ready(self, ready: bool = True):
        """Mark service as ready to accept traffic."""
        self.is_ready = ready
        logger.info(f"Service readiness set to: {ready}")
    
    def add_dependency_check(self, name: str, check_func: Callable):
        """
        Add a dependency health check.
        
        Args:
            name: Dependency name (e.g., 'database', 'redis')
            check_func: Async function that returns True if healthy
        """
        self.dependency_checks[name] = check_func
    
    async def check_dependencies(self) -> Dict[str, Any]:
        """
        Check all dependencies.
        
        Returns:
            Dict with status of each dependency
        """
        results = {}
        
        for name, check_func in self.dependency_checks.items():
            try:
                is_healthy = await asyncio.wait_for(check_func(), timeout=2.0)
                results[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "ok": is_healthy
                }
            except asyncio.TimeoutError:
                results[name] = {"status": "timeout", "ok": False}
            except Exception as e:
                results[name] = {"status": "error", "error": str(e), "ok": False}
        
        return results


# Global health check instance
health_check = HealthCheck()


@router.get("/health", status_code=200)
async def health(response: Response) -> Dict[str, Any]:
    """
    Liveness probe endpoint.
    
    Returns HTTP 200 if service is alive (process running).
    Used by Kubernetes to restart unhealthy pods.
    """
    return {
        "status": "healthy",
        "service": "somaagent",
    }


@router.get("/ready", status_code=200)
async def ready(response: Response) -> Dict[str, Any]:
    """
    Readiness probe endpoint.
    
    Returns HTTP 200 if service is ready to accept traffic.
    Checks dependencies and initialization status.
    Used by Kubernetes to route traffic.
    """
    if not health_check.is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "ready": False,
            "message": "Service still initializing"
        }
    
    # Check dependencies
    dependencies = await health_check.check_dependencies()
    
    all_healthy = all(dep.get("ok", False) for dep in dependencies.values())
    
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "ready": False,
            "dependencies": dependencies
        }
    
    return {
        "status": "ready",
        "ready": True,
        "dependencies": dependencies
    }


@router.get("/healthz", status_code=200)
async def healthz() -> Dict[str, str]:
    """Alternative health endpoint (common Kubernetes convention)."""
    return {"status": "ok"}


@router.get("/readyz", status_code=200)
async def readyz(response: Response) -> Dict[str, Any]:
    """Alternative readiness endpoint (common Kubernetes convention)."""
    return await ready(response)


def create_health_router(
    service_name: str,
    version: str = "1.0.0",
    dependency_checks: Optional[Dict[str, Callable]] = None
) -> APIRouter:
    """
    Create health router with service-specific configuration.
    
    Args:
        service_name: Name of the service
        version: Service version
        dependency_checks: Optional dict of dependency check functions
        
    Returns:
        Configured APIRouter
    """
    # Add dependency checks if provided
    if dependency_checks:
        for name, check_func in dependency_checks.items():
            health_check.add_dependency_check(name, check_func)
    
    # Add version endpoint
    @router.get("/version")
    async def version_endpoint():
        return {
            "service": service_name,
            "version": version,
            "ready": health_check.is_ready
        }
    
    return router
