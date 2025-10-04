⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaSuite Observability Console & Metrics Activation

This guide documents the production-ready metrics pipeline for SomaGent without Grafana. All telemetry feeds into the SomaSuite Observability Console, which consumes Prometheus metrics, Loki logs, and Tempo traces to render dashboards and alerts purpose-built for the SomaSuite experience.

## Objectives
- Ensure **every service exports real Prometheus metrics** at `/metrics` with zero mocks.
- Provide a **repeatable deployment path** that installs Prometheus without bundling Grafana.
- Describe how the **SomaSuite Observability Console** ingests Prometheus data to render dashboards and alerting views.
- Enumerate the **core dashboards** that must exist in SomaSuite for initial launch.

## Metrics Surface Inventory
| Service | Metrics Endpoint | Key Families |
|---------|-----------------|--------------|
| `gateway-api` | `/metrics` | request latency histogram, tool invocation counters, HTTP status counts |
| `orchestrator` | `/metrics` | workflow durations, policy decision counters, Temporal queue depth |
| `identity-service` | `/metrics` | token issuance counters, error totals, cache hit ratios |
| `settings-service` | `/metrics` | config read/write latency, cache invalidations |
| `slm-service` | `/metrics` | token usage, latency buckets, refusal/error counters |
| `memory-gateway` | `/metrics` | recall latency, cache hit ratio, SomaBrain roundtrip timings |
| `notification-service` | `/metrics` | delivery latency, queue backlog gauges |
| `jobs` | `/metrics` | job lifecycle counters, worker concurrency gauges |
| `task-capsule-repo` | `/metrics` | submission counts, approval latency histograms |
| `analytics-service` | `/metrics` | dashboard render latency, anomaly detections |
| `constitution-service` | `/metrics` | signature verification counters, cache refresh events |

Every new service **must** expose the Prometheus endpoint using `prometheus-client>=0.20.0` and register metrics under the `somagent_` namespace.

## Deployment Steps
1. **Install Prometheus** via Helm:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus prometheus-community/prometheus \
     --namespace monitoring --create-namespace
   ```
2. **Port-forward Prometheus** to validate scrapes:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-server 9090:80
   ```
3. **Verify scrape targets** – under the Prometheus UI (`Status ▸ Targets`) ensure each SomaGent service reports `UP` with TLS/Metrics auth managed via Kubernetes service discovery.
4. **Publish to SomaSuite** – The SomaSuite Observability Console pulls Prometheus data through the `/api/v1/query_range` endpoint. Configure the console with:
   - Prometheus base URL
   - API key/Basic auth for restricted environments (stored in Vault and injected at runtime)
   - Dashboard manifests located in `observability/manifests/*.yaml`
5. **Register dashboards** – Use the SomaSuite CLI to push dashboard definitions:
   ```bash
   somasuite dashboards publish observability/manifests/agent-one-sight.yaml
   somasuite dashboards publish observability/manifests/policy-enforcement.yaml
   somasuite dashboards publish observability/manifests/slm-telemetry.yaml
   ```

## Required SomaSuite Dashboards
- **Agent One Sight** – Session latency, token usage, policy denials, capsule throughput.
- **SLM Telemetry** – Token histogram, refusal rate, latency per provider, queue depth.
- **Policy Enforcement** – Constitution hash versions, deny/allow counters, human approval backlog.
- **Memory Health** – Recall latency, replay backlog, SomaBrain availability, Redis cache hit ratio.
- **Notification Delivery** – Queue backlog, notification latency, error rates by channel.

Each dashboard is defined in YAML exports that SomaSuite stores internally; Grafana JSON is **not** used anywhere in the project.

## Alerting & Notifications
- Prometheus Alertmanager remains the signal source. Alerts feed into the notification-service via the `/v1/notifications` endpoint tagged by severity.
- SomaSuite renders alert timelines directly from notification events and Prometheus alert state.
- Required alerts: `orchestrator_high_latency`, `policy_denials_spike`, `slm_refusal_rate`, `memory_backlog_high`, `notification_delivery_failures`.

## Runbook Integration
- Cross-region observability and DR runbooks reference SomaSuite dashboards instead of Grafana imports.
- `docs/runbooks/cross_region_observability.md` has been updated to call out SomaSuite-specific panel templates.

## Next Steps
1. Migrate existing Grafana JSON assets (if any remain off-repo) into SomaSuite dashboard YAML format.
2. Extend Prometheus scrape configs to include Temporal, Kafka, and external tool adapters.
3. Embed SomaSuite dashboard links into the Admin Console (Agent One Sight view).
4. Automate dashboard validation in CI: fail builds if required metrics disappear or change type.
```}