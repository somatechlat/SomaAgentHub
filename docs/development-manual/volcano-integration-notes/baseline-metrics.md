# Volcano Integration Baseline Metrics Plan

**Purpose:** Describe how to capture pre-Volcano runtime metrics so we can quantify improvements and detect regressions during rollout.

**Audience:** Platform engineers, SREs, data analysts supporting the integration.

**Last Updated:** 2025-10-17

---

## 1. Metric Sources

| Source | Access Method | Key Signals |
|--------|---------------|-------------|
| Prometheus (`infra/monitoring/prometheus.yml`) | `http://prometheus:9090/api/v1/query` | `temporal_workflow_task_schedule_to_start_latency_bucket`, `orchestrator_active_sessions`, `ray_worker_cpu_seconds_total` (once enabled) |
| Temporal | `tctl` or gRPC metrics endpoint (`temporal:9090`) | Workflow backlog, task queue depth, namespace throughput |
| Ray (embedded) | Ray dashboard (enable `RAY_DASHBOARD_AGENT_LISTEN_PORT`) | Job runtime, worker memory/CPU usage |
| Service logs | Loki queries (if deployed) | Activity execution durations, retries |

---

## 2. Collection Steps

### 2.0 Sandbox Validation Run

1. Ensure queues are applied: `kubectl apply -f infra/k8s/local/volcano/queues.yaml`.
2. Submit the sample job: `kubectl apply -f infra/k8s/local/volcano/sample-session-job.yaml`.
  - Or run `scripts/volcano/run-sample-session.sh` to automate steps 1–4 and collect artifacts.
3. Capture PodGroup state: `kubectl describe podgroup session-sample > artifacts/session-pg.txt`.
4. Store job logs: `kubectl logs job/session-sample > artifacts/session-job.log`.
5. (Optional) Tear down the sample job: `scripts/volcano/cleanup-sample.sh`.

### 2.1 Prometheus Snapshot

```bash
PROM_URL="http://localhost:9090"   # Port-forward or use service DNS
START="2025-10-01T00:00:00Z"
END="2025-10-07T23:59:59Z"

# Export p95 schedule-to-start latency for session workflow
curl -sG "${PROM_URL}/api/v1/query_range" \
  --data-urlencode "query=histogram_quantile(0.95, sum(rate(temporal_workflow_task_schedule_to_start_latency_bucket{workflow_type=\"session-start-workflow\"}[5m])) by (le))" \
  --data-urlencode "start=${START}" \
  --data-urlencode "end=${END}" \
  --data-urlencode "step=60" > baseline-session-latency.json
```

Repeat for:
- `temporal_workflow_task_schedule_to_start_latency_bucket{workflow_type="marketing-campaign"}`
- `temporal_workflow_task_schedule_to_start_latency_bucket{workflow_type="multi-agent-orchestration-workflow"}`
- `process_cpu_seconds_total{service="orchestrator"}`

### 2.2 Temporal Queue Depth

```bash
kubectl exec -n somaagent deployment/orchestrator -- \
  tctl --address temporal-frontend.somaagent:7233 \
  taskqueue describe --taskqueue somagent.session.workflows --taskqueue-type workflow
```

Record `Backlog` and `ReadLevel` values daily to track load before Volcano changes.

### 2.3 Ray Metrics (Enable if disabled)

1. Set env vars in orchestrator deployment:
   - `RAY_DASHBOARD_AGENT_LISTEN_PORT=8265`
   - `RAY_GRAFANA_HOST` if using Grafana integration.
2. Port-forward or scrape Ray metrics endpoint `http://<pod-ip>:8265/metrics` and export `ray_task_runtime_avg_ms`.

### 2.4 Marketing Workflow Duration

Query Temporal for workflow histories and export durations:

```bash
WORKFLOWS=$(tctl workflow list --query "WorkflowType='MarketingCampaignWorkflow'" --fields WorkflowId,RunId --limit 50)
# Iterate to fetch completion time via tctl or Temporal API.
```

Store results in CSV alongside Prometheus exports for trend analysis.

---

## 3. Storage & Reporting

- Commit raw JSON/CSV exports to a dedicated object store or analytics bucket (avoid committing large files to git).
- Summarise findings in `docs/development-manual/volcano-integration-notes/retro.md` at the end of Sprint 1.
- Update Grafana dashboards to display baselines vs. post-Volcano metrics.

---

## 4. Open Items

- [ ] Enable Ray dashboard metrics in dev/staging clusters.
- [ ] Confirm Loki log queries for marketing saga step durations.
- [ ] Automate Prometheus exports via GitHub Action or cron job in monitoring namespace.

---

*Update this plan as new signals or tooling are introduced.*
