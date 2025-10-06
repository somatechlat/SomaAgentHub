"""OPA (Open Policy Agent) client for SomaGent platform.

This module provides a reusable HTTP client for evaluating policies via OPA's
REST API. It can be used by gateway, orchestrator, and other services.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from functools import lru_cache

import httpx
from fastapi import HTTPException, status


class OPAClient:
    """Client for Open Policy Agent policy evaluation."""

    def __init__(self, opa_url: str, timeout: float = 5.0):
        """Initialize OPA client.
        
        Args:
            opa_url: Base URL for OPA server (e.g., http://opa:8181)
            timeout: Request timeout in seconds
        """
        self.opa_url = opa_url.rstrip("/")
        self.timeout = timeout

    async def evaluate_policy(
        self,
        policy_path: str,
        input_data: Dict[str, Any],
        rule: str = "allow",
    ) -> Dict[str, Any]:
        """Evaluate a policy via OPA's REST API.
        
        Args:
            policy_path: Policy path (e.g., "somagent/session/authorization")
            input_data: Input data for the policy evaluation
            rule: Rule name to evaluate (default: "allow")
            
        Returns:
            Dictionary with evaluation result, typically containing:
                - allowed: bool (whether the action is allowed)
                - reason: str (optional explanation)
                - metadata: dict (additional context)
                
        Raises:
            HTTPException: If OPA is unreachable or returns an error
        """
        url = f"{self.opa_url}/v1/data/{policy_path}/{rule}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"input": input_data},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                # httpx.Response.json() is sync, but in tests it may be an async mock returning a coroutine.
                result = response.json()
                # If the mock returns a coroutine, await it.
                if hasattr(result, "__await__"):
                    result = await result
                
                # OPA returns {"result": <policy_output>}
                policy_result = result.get("result")
                
                if isinstance(policy_result, bool):
                    return {"allowed": policy_result}
                if isinstance(policy_result, dict):
                    return policy_result
                return {"allowed": bool(policy_result)}
        
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"OPA policy evaluation timed out: {policy_path}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OPA policy evaluation failed: {exc.response.status_code}"
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OPA policy evaluation error: {str(exc)}"
            ) from exc

    async def check_authorization(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Convenience method to check if an action is authorized.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            action: Action being performed (e.g., "create", "read", "delete")
            resource: Resource being accessed (e.g., "session", "capsule")
            context: Additional context data
            
        Returns:
            True if authorized, False otherwise
        """
        input_data = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "context": context or {},
        }
        
        result = await self.evaluate_policy(
            policy_path="somagent/authorization",
            input_data=input_data,
            rule="allow"
        )
        
        return result.get("allowed", False)

    async def evaluate_constitution(
        self,
        action_type: str,
        payload: Dict[str, Any],
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Evaluate an action against constitutional policies.
        
        Args:
            action_type: Type of action (e.g., "tool_invocation", "model_selection")
            payload: Action payload
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary with evaluation result:
                - allowed: bool
                - violations: list of violation messages
                - score: float (compliance score 0-1)
        """
        input_data = {
            "action_type": action_type,
            "payload": payload,
            "tenant_id": tenant_id,
        }
        
        return await self.evaluate_policy(
            policy_path="somagent/constitution",
            input_data=input_data,
            rule="evaluate"
        )

    async def health_check(self) -> bool:
        """Check if OPA server is reachable and healthy.
        
        Returns:
            True if OPA is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.opa_url}/health")
                return response.status_code == 200
        except Exception:
            return False


@lru_cache
def get_opa_client() -> OPAClient:
    """Return a cached OPA client instance from environment variables.
    
    Required environment variables:
        OPA_URL: OPA server URL (default: http://opa:8181)
        OPA_TIMEOUT: Request timeout in seconds (default: 5.0)
    """
    opa_url = os.getenv("OPA_URL", "http://opa:8181")
    timeout = float(os.getenv("OPA_TIMEOUT", "5.0"))
    
    return OPAClient(opa_url=opa_url, timeout=timeout)
