# Infrastructure Reference

**Operational manifests and provisioning code for SomaAgentHub**

> This directory contains the infrastructure-as-code assets used to provision local, staging, and production environments.

---

## Directory Map

| Path | Purpose |
| --- | --- |
| `infra/k8s/` | Raw Kubernetes manifests for core services (gateway, orchestrator, policy, identity, etc.). |
| `infra/helm/` | Shared Helm helpers and values overlays. |
| `infra/temporal/` | Docker Compose files for local Temporal clusters. |
| `infra/airflow/` | Airflow docker-compose for ETL jobs and testing. |
| `infra/flink/` | Flink docker-compose resources for streaming jobs. |
| `infra/clickhouse/` | ClickHouse configs and bootstrap scripts. |
| `infra/postgres/` | Postgres configs, migrations, and backup scripts. |
| `infra/seeds/` | Seed data for bootstrapping environments. |
| `infra/monitoring/` | Observability stack manifests (Prometheus, Grafana, Loki). |
| `infra/terraform/` | Terraform modules for cloud infrastructure (VPC, clusters, databases). |

---

## Usage Patterns

- **Local Development**: Use `make dev-up` for Temporal and Redis; `infra/temporal/docker-compose.yml` provides the stack. `infra/postgres` and `infra/clickhouse` include scripts for schema setup.
- **Production Deployments**: Prefer the Helm chart in `k8s/helm/soma-agent`. Raw manifests in `infra/k8s/` serve as canonical templates and examples.
- **Infrastructure as Code**: Terraform modules support AWS region deployments. Run via `make deploy-region` with appropriate `ACTION` (`plan`, `apply`, `destroy`).

---

## Change Management

1. Update manifests and Terraform modules in sync with application changes.
2. Validate with `kubectl apply --dry-run=client` or `terraform plan` before merging.
3. Document significant updates in `docs/changelog.md` and update the relevant guides under `docs/technical-manual/runbooks/` when applicable.
4. Version Helm chart changes and update `Chart.yaml` accordingly.

---

## Observability Integration

- ServiceMonitor resources reside in `k8s/monitoring/`; ensure new services expose `/metrics` and add monitors as needed.
- Alerting rules and dashboards are tracked under `infra/monitoring/`; update runbooks when adding alerts.

---

## Conventions

- All manifests must declare resource requests/limits, readiness and liveness probes, and security contexts.
- Use namespaces explicitly (`soma-agent-hub`, `observability`, etc.).
- Secrets should reference Vault-managed or sealed resources; avoid committing plaintext credentials.

---

For contributions, coordinate with the Platform Operations team (`#soma-ops`).
