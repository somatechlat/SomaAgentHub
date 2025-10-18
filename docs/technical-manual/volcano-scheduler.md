# Volcano Scheduler Integration

**Purpose:** Document how SomaAgentHub deploys, configures, and operates the Volcano batch scheduler.

**Audience:** Platform engineers, SREs, release managers.

**Last Reviewed:** 2025-10-17

---

## Prerequisites

- Kubernetes cluster running SomaAgentHub base infrastructure (see `docs/technical-manual/deployment.md`).
- Cluster-admin permissions to install CRDs and scheduler plugins.
- Access to container registry storing SomaAgentHub images.
- Familiarity with Temporal workflows (`services/orchestrator`) and batch workload requirements.

---

## Deployment Overview

1. Install Volcano CRDs and controllers.
2. Configure queues, PodGroups, and priority policies aligned to agent workloads.
3. Wire orchestrator job submissions to reference Volcano-specific annotations.
4. Expose Volcano metrics for observability and verify admission webhooks.

### Installation Steps (Sandbox)

```bash
# 1. Add Volcano Helm repo
helm repo add volcano https://volcano-sh.github.io/helm-charts
helm repo update

# 2. Deploy Volcano into the workload namespace
NAMESPACE=soma-agent-hub
helm upgrade --install volcano volcano/volcano \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --set controller.image.tag=v1.9.0 \
  --set scheduler.image.tag=v1.9.0 \
  --set admission.image.tag=v1.9.0

# 3. Confirm components are ready
kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=volcano-scheduler
kubectl get validatingwebhookconfiguration | grep volcano

# 4. Seed sandbox queues and submit a sample job
kubectl apply -f infra/k8s/local/volcano/queues.yaml
kubectl apply -f infra/k8s/local/volcano/sample-session-job.yaml

# 5. Grant orchestrator RBAC permissions (cluster or staging)
kubectl apply -f infra/k8s/orchestrator-rbac.yaml

# 6. Monitor job execution
kubectl get podgroup session-sample
kubectl logs job/session-sample

# Convenience scripts (optional)
scripts/volcano/run-sample-session.sh    # apply, wait, and collect artifacts
scripts/volcano/cleanup-sample.sh        # remove sample resources when finished

> The orchestrator container image now bundles `kubectl` so jobs can be submitted directly from the worker pods.
```

> Tip: To provision a local sandbox quickly, run `scripts/volcano/bootstrap-kind.sh`. The script creates a three-node kind cluster and installs Volcano using the configuration above.

### Production Configuration Checklist

| Item | Description | Status |
|------|-------------|--------|
| Queue definitions | Define `high-priority`, `standard`, `background` queues with quotas | ☐ |
| PodGroup defaults | Set gang sizes matching Temporal task requirements | ☐ |
| Admission policies | Enable SLA, fair-share, and preemption plugins | ☐ |
| Feature flags | Toggle `ENABLE_VOLCANO_SCHEDULER` in service configs | ☐ |
| Rollback plan | Document steps to revert to native scheduler | ☐ |

Update `infra/helm/` overlays with queue YAML fragments once validated.

---

## Configuration Details

### Queue YAML Template

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: standard
spec:
  weight: 1
  reclaimable: true
  capability:
    cpu: "200"
    memory: "512Gi"
```

### PodGroup Annotations for Orchestrator Jobs

```yaml
metadata:
  annotations:
    scheduling.k8s.io/group-name: "research-workflow"
    volcano.sh/queue-name: "standard"
    volcano.sh/task-spec: |
      {
        "minMember": 3,
        "minResources": {
          "cpu": "6",
          "memory": "24Gi"
        }
      }
```

Ensure orchestrator job templates emitted by Temporal include these annotations when the Volcano feature flag is enabled.

---

## Verification

| Step | Command | Expected Result |
|------|---------|-----------------|
| 1. CRDs installed | `kubectl get crd | grep volcano` | `queues.scheduling.volcano.sh` present |
| 2. Scheduler active | `kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=volcano-scheduler` | Pods in `Running` state |
| 3. Queue health | `kubectl get queue` | Queues show correct status and capability |
| 4. PodGroup admission | `kubectl describe podgroup <name>` | `Status: Running` with all members bound |
| 5. Metrics scrape | Check Prometheus targets | Volcano exporter targets `up == 1` |

If any step fails, consult the runbook (`./runbooks/volcano-operations.md`).

---

## Monitoring & Alerts

- **Metrics Source:** Prometheus scrapes scheduler/controller endpoints via the `volcano-control-plane` job defined in `infra/monitoring/prometheus.yml`, the scheduler `ServiceMonitor`, and controller `PodMonitor` manifests under `k8s/monitoring/servicemonitors.yaml` (controller metrics exposed on port `10252`).
- **Key Metrics:**
  - `volcano_queue_pending_pods` / `volcano_queue_running_pods` — backlog and admitted workload by queue.
  - `volcano_job_scheduling_duration_seconds_bucket` — histogram for scheduling latency (combine with `histogram_quantile` for P95).
  - `volcano_pod_preemptions_total` — preemption activity per queue.
  - `process_resident_memory_bytes{job=~"volcano-control-plane.*"}` — scheduler/controller resource footprint.
- **Dashboards:** Grafana **Volcano Scheduler Operations** dashboard (`infra/monitoring/grafana/dashboards/volcano-operations.json`) tracks queue depth, scheduling latency (average & P95), PodGroup wait distribution, and preemption frequency.
- **Alerting Rules:** `infra/monitoring/alerting-rules.yml` adds `VolcanoQueueBacklog`, `VolcanoSchedulingLatencyHigh`, and `VolcanoPreemptionSpike` to surface backlog, latency, and preemption anomalies.

Integrate scrapes in `infra/monitoring/prometheus.yml` and deploy the monitoring assets via `k8s/monitoring`.

---

## Common Errors & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pods remain in `Pending` with `Unschedulable` | Gang size exceeds available resources | Adjust queue quotas or reduce `minMember` requirement. |
| Admission webhook rejects jobs | Missing required annotations or invalid JSON payload | Validate annotations; test with `kubectl apply --dry-run=server`. |
| Scheduler restarts repeatedly | Version mismatch or insufficient permissions | Align controller/scheduler versions; verify RBAC roles. |
| Metrics missing from Prometheus | ServiceMonitor not deployed | Add ServiceMonitor for Volcano namespace. |

---

## Security Considerations

- Restrict queue management via RBAC; only platform admins manage CRDs.
- Enforce namespace-scoped quotas to prevent noisy neighbor issues.
- Audit scheduler configuration changes through GitOps; no manual edits in production.
- Keep Volcano images pinned to approved digests and monitor CVE feeds.

---

## Change Management

1. Update infrastructure manifests via pull request.
2. Run `markdownlint` and link checker on documentation changes.
3. Rollout using progressive delivery (staging → canary → full).
4. Capture post-change metrics and record a summary in the change log (`docs/changelog.md`).

---

## References

- Volcano Documentation: https://volcano.dev/docs
- Runbook: `docs/technical-manual/runbooks/volcano-operations.md`
- Development Roadmap: `docs/development-manual/volcano-integration-roadmap.md`
- Temporal-Kubernetes patterns: https://docs.temporal.io/blog/temporal-on-kubernetes

---

*Keep this page in sync with the live deployment scripts. Update "Last Reviewed" whenever the checklist or commands change.*
