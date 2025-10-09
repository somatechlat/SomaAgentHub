# Environment Variables Reference

Last Updated: October 9, 2025

## Orchestrator

- TEMPORAL_HOST (alias of TEMPORAL_TARGET_HOST)
- TEMPORAL_NAMESPACE (default: default)
- TEMPORAL_TASK_QUEUE (default: somagent.session.workflows)
- POLICY_ENGINE_URL (default: http://policy-engine:8000/v1/evaluate)
- IDENTITY_SERVICE_URL (default: http://identity-service:8000/v1/tokens/issue)
- SOMALLM_PROVIDER_URL (default: http://slm-service:1001) [legacy alias supported: SLM_SERVICE_URL]
- SOMALLM_PROVIDER_HEALTH_URL (default: http://slm-service:1001/health) [legacy alias: SLM_HEALTH_URL]
- OTEL_EXPORTER_OTLP_ENDPOINT (optional)

## Gateway API

- OTEL_EXPORTER_OTLP_ENDPOINT (optional)
- AUTH settings (see service README)

## SLM Service

- ENVIRONMENT (default: development)
- ENABLE_OTLP (default: false)
- OTEL_EXPORTER_OTLP_ENDPOINT (optional)

Notes:
- Legacy variables are preserved for backward compatibility where noted.
- Defaults use in-cluster DNS names.
