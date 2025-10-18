# Runbook: Volcano Operations

**Purpose:** Provide step-by-step procedures for monitoring, troubleshooting, and recovering the Volcano scheduler that powers SomaAgentHub batch workloads.

**Audience:** On-call SREs, platform engineers, incident commanders.

**Last Reviewed:** 2025-10-17

---

## Prerequisites

- Familiarity with the Volcano deployment as described in `../volcano-scheduler.md`.
- `kubectl` access with permissions to read and restart resources in the SomaAgentHub namespace.
- Access to Grafana, Prometheus, and Loki dashboards.
- Knowledge of Temporal workflow queue configuration.

---

## Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Check scheduler health | `kubectl get pods -n soma-agent-hub -l app.kubernetes.io/name=volcano-scheduler` | Pods should be `Running`. |
| Inspect queue status | `kubectl get queue` | Look for `STATE` = `Open`. |
| Reapply sandbox queues | `kubectl apply -f infra/k8s/local/volcano/queues.yaml` | Restores default capacities. |
| Describe PodGroup | `kubectl describe podgroup <name>` | Review `Status` and `Events`. |
| Tail scheduler logs | `kubectl logs -n soma-agent-hub deployment/volcano-scheduler -f` | Filter for `Warning`/`Error`. |
| Cleanup sample job | `scripts/volcano/cleanup-sample.sh` | Deletes `session-sample` job/PodGroup artifacts. |
| Verify orchestrator RBAC | `kubectl get rolebinding orchestrator-volcano -n <ns>` | Ensure Volcano permissions remain in place. |

---

## Incident Scenarios

### 1. Jobs Stuck in Pending

**Symptoms:**
- Grafana alert `VolcanoQueuePendingJobsHigh` firing.
- Temporal workflows waiting for execution slots.

**Procedure:**
1. Verify PodGroup status: `kubectl describe podgroup <pg-name>`.
2. Check queue capacity: `kubectl get queue -o yaml` and confirm `capability` suffices.
3. Inspect cluster resources: `kubectl top nodes` and `kubectl get nodes -o wide`.
4. If resources constrained, scale worker nodes or reduce gang size in workload definition.
5. Update queue capability via GitOps manifest if sustainable change required.
6. Document actions in incident ticket and ensure Temporal backlog drains.

**Verification:** `kubectl get podgroup <pg-name>` shows `Running`; queue pending count trending down.

### 2. Scheduler Pod CrashLooping

**Symptoms:**
- `kubectl get pods` shows `CrashLoopBackOff` for scheduler.
- Logs contain configuration errors or permission issues.

**Procedure:**
1. Capture logs: `kubectl logs -n soma-agent-hub deployment/volcano-scheduler --previous`.
2. Compare deployed chart values with Git; ensure versions align.
3. Validate RBAC: `kubectl auth can-i list pods --as system:serviceaccount:soma-agent-hub:volcano-scheduler`.
4. If misconfiguration found, revert to last known good manifest.
5. Restart deployment: `kubectl rollout restart deployment/volcano-scheduler -n soma-agent-hub`.
6. If issue persists, disable feature flag to fall back to native scheduler and escalate.

**Verification:** Scheduler pods running for >10 minutes without restart; workflows resume.

### 3. Admission Webhook Failures

**Symptoms:**
- Workloads rejected with validation errors.
- API server events show `volcano-admission` failures.

**Procedure:**
1. Inspect webhook logs: `kubectl logs -n soma-agent-hub deployment/volcano-admission -f`.
2. Validate CA bundle and certificates; renew if expired.
3. Test job submission with `--dry-run=server` to reproduce error.
4. Update annotations or schema mismatch in orchestrator templates.
5. Redeploy admission component if configuration changed.

**Verification:** `kubectl apply --dry-run=server -f sample-job.yaml` succeeds; new workloads admitted.

### 4. Queue Saturation Causing SLA Breach

**Symptoms:**
- SLA alerts from Temporal or external monitoring.
- Queue metrics show high wait times.

**Procedure:**
1. Identify high-priority workloads and move to `high-priority` queue if necessary.
2. Enable or tune preemption plugin weights in Volcano config.
3. Temporarily increase queue capability via approved change.
4. Communicate capacity state to stakeholders and update status page.

**Verification:** SLA metrics fall back within target range; queue length decreases.

---

## Post-Incident Actions

1. Summarize incident in `docs/development-manual/volcano-integration-notes/daily-journal.md`.
2. File follow-up issues for structural fixes (e.g., capacity planning, alert thresholds).
3. Update this runbook if steps changed or new root causes discovered.
4. Notify release manager if production impact exceeded SLA.

---

## References

- Scheduler deployment guide: `../volcano-scheduler.md`
- Development roadmap: `../../development-manual/volcano-integration-roadmap.md`
- Volcano official troubleshooting: https://volcano.dev/docs/troubleshooting
- Temporal operations manual: `../runbooks/orchestrator.md`

---

*Review this runbook quarterly or after any major Volcano upgrade.*
