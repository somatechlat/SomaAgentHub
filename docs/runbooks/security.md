# Security Hardening Runbook

## Certificates (mTLS)
- Generate service certificates via your PKI (or SPIFFE/SPIRE).
- Configure env vars per service (example):
  - `SOMAGENT_GATEWAY_TLS_CERTFILE`
  - `SOMAGENT_GATEWAY_TLS_KEYFILE`
  - `SOMAGENT_GATEWAY_TLS_CA_CERT`
- Run `uvicorn` or ingress controller with the provided certs.

## Secrets
- Load sensitive keys via env vars or files (see `somagent-secrets` helper).
  - e.g., `SOMAGENT_SLM_VOICE_API_KEY` or `SOMAGENT_SLM_VOICE_API_KEY_FILE`.
- Store credentials in Vault/KMS and inject at runtime (Kubernetes secrets or CI).

## Kafka Security
- Enable SASL/SSL on Kafka and configure ACLs for topics (`notifications.events`, `mao.events`, `slm.requests`).

## Hardening Checklist
- [ ] Rotate certs and secrets regularly.
- [ ] Enable mTLS for inter-service communication.
- [ ] Restrict network access via Kubernetes NetworkPolicies.
- [ ] Run dependency scans (Snyk/Trivy) in CI.
- [ ] Perform regular load & chaos tests (see `tests/perf` and `tests/chaos`).

## Network Policies (Deny-by-Default)
- Apply a namespace-wide default `deny all` policy.
- Allow ingress from the gateway only to orchestrator, identity, policy, memory, and notification services.
- Permit egress from services strictly to their dependencies (e.g., gateway -> orchestrator/policy/tool/slm).
- Expose external traffic only via ingress controller or API gateway; block pod-to-pod access for admin consoles unless explicitly required.
- Example snippets:
  - Gateway allow egress: selector `app=gateway-api` with destinations `app in {orchestrator, policy-engine, tool-service, slm-service, memory-gateway}` on ports 8000/8080.
  - Tool service allow egress only to whitelisted SaaS endpoints via egress gateway (if needed) or queue topics.
- Combine with `NetworkPolicy` logging (Cilium/Calico) for audit evidence.

## Observability Hooks
- Gateway exposes Prometheus metrics at `GET /metrics` with moderation counters (`gateway_moderation_decisions_total`, `gateway_orchestrator_forward_latency_seconds`).
- Tool service exposes `tool_adapter_executions_total`, `tool_adapter_execution_latency_seconds`, and rate limit hits.
- OpenTelemetry spans enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured; spans propagate HTTP headers through gateway → orchestrator/tool services.
