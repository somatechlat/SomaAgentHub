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
