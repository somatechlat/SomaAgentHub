"""Custom Airflow operators for interacting with the SomaAgentHub platform."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import jwt
import requests
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.context import Context


def _generate_service_jwt() -> str:
    """Generate a short-lived JWT for service-to-service calls.

    In development we sign tokens with the shared SOMAGENT_GATEWAY_JWT_SECRET so
    the Gateway accepts requests coming from Airflow without a dedicated IdP.
    Production deployments should override this environment-based signer by
    mounting a service account token and setting SOMAGENT_AIRFLOW_JWT static
    token instead.
    """

    static_token = os.getenv("SOMAGENT_AIRFLOW_JWT")
    if static_token:
        return static_token

    secret = os.getenv("SOMAGENT_GATEWAY_JWT_SECRET")
    if not secret:
        raise AirflowException("Gateway JWT secret not configured for Airflow")

    now = int(time.time())
    payload = {
        "iss": "airflow",
        "sub": os.getenv("SOMAGENT_AIRFLOW_SUBJECT", "airflow-service"),
        "tenant_id": os.getenv("SOMAGENT_AIRFLOW_TENANT", "demo"),
        "capabilities": ["scheduler", "system"],
        "iat": now,
        "exp": now + int(os.getenv("SOMAGENT_AIRFLOW_JWT_TTL", "600")),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


@dataclass
class TemporalStartConfig:
    """Configuration payload for kicking off Temporal workflows via the gateway."""

    prompt: str
    tenant: str
    user: str
    metadata: Optional[Dict[str, Any]] = None


class SomaGatewayTemporalOperator(BaseOperator):
    """Trigger the SomaAgentHub gateway to start a Temporal session workflow."""

    template_fields = ("prompt", "tenant", "user", "metadata", "capsule_id")

    def __init__(
        self,
        *,
        prompt: str,
        tenant: str,
        user: str,
        metadata: Optional[Dict[str, Any]] = None,
        capsule_id: Optional[str] = None,
        gateway_url: Optional[str] = None,
        timeout_seconds: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.prompt = prompt
        self.tenant = tenant
        self.user = user
        self.metadata = metadata or {}
        self.capsule_id = capsule_id
        self.gateway_url = gateway_url or os.getenv("SOMAGENT_GATEWAY_URL", "http://gateway-api:8000")
        self.timeout_seconds = timeout_seconds

    def execute(self, context: Context) -> Dict[str, Any]:  # noqa: D401
        token = _generate_service_jwt()
        url = f"{self.gateway_url}/v1/sessions"
        payload: Dict[str, Any] = {
            "prompt": self.prompt,
            "metadata": {**self.metadata, "requested_by": self.user, "tenant": self.tenant},
        }
        if self.capsule_id:
            payload["capsule_id"] = self.capsule_id

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        self.log.info("Triggering Gateway session at %s", url)
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout_seconds)
        if resp.status_code >= 400:
            raise AirflowException(
                f"Gateway call failed with status {resp.status_code}: {resp.text}"
            )

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:  # noqa: BLE001
            raise AirflowException(f"Gateway response was not JSON: {resp.text}") from exc

        self.log.info("Gateway accepted session request: session_id=%s", data.get("session_id"))
        return data
