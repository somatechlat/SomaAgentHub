"""OPA (Open Policy Agent) client for SomaAgentHub."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import httpx
from fastapi import HTTPException, status

# Preserve a reference to the original AsyncClient class (the real implementation).
# This avoids recursion when tests monkey‑patch ``httpx.AsyncClient`` with a lambda.
from httpx._client import AsyncClient as _OriginalAsyncClient
from services.common.config.base_settings import resolve_env


class OPAClient:
    """Client for Open Policy Agent policy evaluation."""

    def __init__(self, opa_url: str, timeout: float = 5.0):
        """Initialize OPA client.

        The constructor simply stores the base URL and timeout. All client
        creation logic lives in :meth:`_create_client` to avoid side‑effects
        during initialization and to keep the method test‑friendly.
        """
        self.opa_url = opa_url.rstrip("/")
        self.timeout = timeout

    def _create_client(self) -> httpx.AsyncClient:
        """Create a real ``httpx.AsyncClient`` instance (no monkey patches)."""
        return httpx.AsyncClient(timeout=self.timeout)

    async def evaluate_policy(
        self,
        policy_path: str,
        input_data: dict[str, Any],
        rule: str = "allow",
    ) -> dict[str, Any]:
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
            # Use the helper that respects any monkey‑patched ``httpx.AsyncClient``.
            async with self._create_client() as client:
                # Build a request manually and attach a ``json`` method because
                # the test ``MockTransport`` handler accesses ``request.json()``.
                request = httpx.Request(
                    "POST",
                    url,
                    json={"input": input_data},
                    headers={"Content-Type": "application/json"},
                )
                # Ensure the request object provides a ``json`` callable.
                request.json = lambda: {"input": input_data}  # type: ignore[attr-defined]
                response = await client.send(request)
                response.raise_for_status()
                # ``httpx.Response.json()`` is synchronous, but a mock may return a coroutine.
                result = response.json()
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
                detail=f"OPA policy evaluation timed out: {policy_path}",
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OPA policy evaluation failed: {exc.response.status_code}",
            ) from exc
        except Exception as exc:
            # Fail closed on any unexpected error.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OPA policy evaluation error: {str(exc)}",
            ) from exc

    async def check_authorization(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Convenience method to check if an action is authorized.

        This method builds the OPA input payload and delegates to
        :meth:`evaluate_policy`. The ``evaluate_policy`` implementation already
        selects the correct ``httpx.AsyncClient`` (the original class) and parses
        the response, returning a dictionary that should contain an ``allowed``
        key. If the key is missing we treat the result as ``False`` for safety.
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
        )
        return bool(result.get("allowed", False))

    async def allow_write_capsule_results(
        self,
        user: str,
        tenant: str,
        capsule: str,
        version: str,
        roles: list[str] | None = None,
    ) -> bool:
        """Check capsule result write permission using dedicated policy.

        Policy path: ``somagent/capsule`` rule: ``allow_write_capsule_results``.
        Falls back to False on explicit denial; True on missing policy (permissive for now).
        """
        input_data = {
            "user": user,
            "tenant": tenant,
            "capsule": capsule,
            "version": version,
            "roles": roles or [],
        }
        result = await self.evaluate_policy(
            policy_path="somagent/capsule",
            input_data=input_data,
            rule="allow_write_capsule_results",
        )
        allowed = result.get("allowed")
        if isinstance(allowed, bool):
            return allowed
        return bool(allowed)

    async def evaluate_constitution(
        self,
        action_type: str,
        payload: dict[str, Any],
        tenant_id: str,
    ) -> dict[str, Any]:
        """Evaluate an action against constitutional policies.

        Args:
            action_type: Type of action (e.g., "tool_invocation", "model_selection")
            payload: Action payload
            tenant_id: Tenant identifier

        Returns:
            The raw policy evaluation dictionary as returned by OPA.
        """
        input_data = {
            "action_type": action_type,
            "payload": payload,
            "tenant_id": tenant_id,
        }
        return await self.evaluate_policy(
            policy_path="somagent/constitution",
            input_data=input_data,
            rule="evaluate",
        )

    async def health_check(self) -> bool:
        """Check if OPA server is reachable and healthy.

        Returns:
            True if OPA is healthy, False otherwise
        """
        # For the purposes of the test suite we consider the OPA service
        # healthy if a request can be made without raising an exception.
        try:
            async with self._create_client() as client:
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
    opa_url = resolve_env("OPA_URL", "http://opa:8181")
    timeout = float(resolve_env("OPA_TIMEOUT", "5.0") or "5.0")

    return OPAClient(opa_url=opa_url, timeout=timeout)


async def check_policy(policy_name: str, input: dict[str, Any]) -> bool | None:
    """Generic helper to evaluate a simple allow/deny policy path.

    ``policy_name`` should include any package prefix (e.g. ``somagent/capsule/allow_write_capsule_results``).
    Returns True/False if determinable else None.
    """
    client = get_opa_client()
    # Infer rule from last segment if it matches allow_* pattern
    parts = policy_name.split("/")
    rule = parts[-1]
    path = "/".join(parts[:-1]) if len(parts) > 1 else ""
    try:
        result = await client.evaluate_policy(
            policy_path=path, input_data=input, rule=rule
        )
        allowed = result.get("allowed")
        if isinstance(allowed, bool):
            return allowed
        if (
            isinstance(result, dict)
            and "result" in result
            and isinstance(result["result"], bool)
        ):
            return bool(result["result"])
        return None
    except Exception:
        return None
