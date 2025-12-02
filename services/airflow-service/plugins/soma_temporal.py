        """Custom Airflow operators for interacting with the SomaAgentHub platform."""

        from __future__ import annotations

        import json
        import os
        from dataclasses import dataclass
        from typing import Any

        import requests
        from airflow.exceptions import AirflowException
        from airflow.models import BaseOperator
        from airflow.utils.context import Context
        from services.common.config.base_settings import resolve_env


        def _load_bearer_token() -> str:
            """Load a bearer token for service-to-service calls.

            Requires a real token set via `SOMA_AGENT_HUB_AIRFLOW_JWT` (or `SOMA_AGENT_HUB_BEARER_TOKEN`).
            Generate one via the Identity Service `/v1/tokens/issue` endpoint.
            """
            token = resolve_env("SOMA_AGENT_HUB_AIRFLOW_JWT") or resolve_env("SOMA_AGENT_HUB_BEARER_TOKEN")
            if not token:
                raise AirflowException(
                "Missing bearer token. Set SOMA_AGENT_HUB_AIRFLOW_JWT (or SOMA_AGENT_HUB_BEARER_TOKEN)."
                )
                return token


                @dataclass
                class TemporalStartConfig:
                    """Configuration payload for kicking off Temporal workflows via the gateway."""

                    prompt: str
                    tenant: str
                    user: str
                    metadata: dict[str, Any] | None = None


                    class SomaGatewayTemporalOperator(BaseOperator):
                        """Trigger the SomaAgentHub gateway to start a Temporal session workflow."""

                        template_fields = ("prompt", "tenant", "user", "metadata", "capsule_id")

                        def __init__(
                        self,
                        *,
                        prompt: str,
                        tenant: str,
                        user: str,
                        metadata: dict[str, Any] | None = None,
                        capsule_id: str | None = None,
                        gateway_url: str | None = None,
                        timeout_seconds: int = 30,
                        **kwargs: Any,
                        ) -> None:
                            super().__init__(**kwargs)
                            self.prompt = prompt
                            self.tenant = tenant
                            self.user = user
                            self.metadata = metadata or {}
                            self.capsule_id = capsule_id
                            self.gateway_url = gateway_url or resolve_env(
                            "SOMA_AGENT_HUB_GATEWAY_URL", "http://gateway-api:8000"
                            )
                            self.timeout_seconds = timeout_seconds

                            def execute(self, context: Context) -> dict[str, Any]:  # noqa: D401
                            token = _load_bearer_token()
                            url = f"{self.gateway_url}/v1/sessions"
                            payload: dict[str, Any] = {
                            "prompt": self.prompt,
                            "metadata": {
                            **self.metadata,
                            "requested_by": self.user,
                            "tenant": self.tenant,
                            },
                            }
                            if self.capsule_id:
                                payload["capsule_id"] = self.capsule_id

                                headers = {
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                                }

                                self.log.info("Triggering Gateway session at %s", url)
                                resp = requests.post(
                                url, json=payload, headers=headers, timeout=self.timeout_seconds
                                )
                                if resp.status_code >= 400:
                                    raise AirflowException(
                                    f"Gateway call failed with status {resp.status_code}: {resp.text}"
                                    )

                                    try:
                                        data = resp.json()
                                        except json.JSONDecodeError as exc:  # noqa: BLE001
                                        raise AirflowException(
                                        f"Gateway response was not JSON: {resp.text}"
                                        ) from exc

                                        self.log.info(
                                        "Gateway accepted session request: session_id=%s", data.get("session_id")
                                        )
                                        return data
