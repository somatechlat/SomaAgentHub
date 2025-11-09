# Infra & Ops Architecture Addendum

## Cluster & Network
- Namespaces per domain (hub, build, policy, pricing, shared).
- Ingress via Istio or Gateway API; internal mTLS via mesh; NetworkPolicies for least privilege.
- Blue/green or canary for Hub and Gateway services.

## Data Layer
- Postgres (config/catalog), ClickHouse (audit/usage), Qdrant (embeddings), Redis (quotas/rate-limits), Object Store (artifacts).
- Encryption at rest; backup/restore runbooks; PITR where applicable.

## Eventing & Processing
- Kafka: `llm.usage`, `billing.receipts`, `audit.events`.
- Flink/Airflow: aggregation jobs, reconciliation, retention compaction.

## Secrets & Identity
- Vault: provider keys, Stripe, DB creds; templating sidecars.
- SPIFFE/SPIRE identities for services; RBAC policy (K8s + OPA/ABAC as needed).
- Optional OpenFGA for fine-grained permissions mapping to roles.

## Observability
- Prometheus, Loki, Tempo/Grafana; OTel collectors per namespace.
- Dashboards per domain (Hub, Build, Policy, Pricing); alert taxonomy and on-call runbooks.

## CI/CD & Supply Chain
- Build: SBOM (Syft), scan (Trivy), cosign sign & verify; provenance attestations.
- Promotion: staging → prod with policy gates; helm chart versioning & linting.

## DR & Multi-Region
- RPO/RTO targets per store; async replication strategy; failover drills; DNS or mesh-based traffic shift.

## Capacity & SLOs
- HPA/VPA tuned to tokens/sec and request concurrency; budgets tracked.
- SLOs: Hub p50<200ms/p95<800ms; Policy p95<50ms; Build p95<5m minimal build.

## Config Standards
- Env var matrix: `LLM_HUB_URL`, `{SERVICE}_URL`, timeouts, auth headers, telemetry toggles.
- Single config loader (pydantic) per service with shared base.

## Cleanup & Consolidation
- Remove duplicates (`object-store` vs `object_store`, `capsule-repo` vs `capsule_repo`).
- Removed legacy `slm-service` and `model-proxy` stubs; LLM Hub is authoritative.

## Acceptance
- Mesh mTLS enforced; secrets from Vault; dashboards live; DR runbook validated quarterly.
