# RFC: Volcano Scheduler Integration Architecture

**Status:** Draft

**Authors:** Platform Engineering Guild

**Last Updated:** 2025-10-17

---

## 1. Purpose

Define the target architecture for introducing the Volcano batch scheduler into SomaAgentHub so that multi-agent workloads gain gang scheduling, fair-share quotas, and SLA-aware preemption without regressing existing Temporal-based orchestration.

---

## 2. Goals

- Externalise resource-intensive activities (Ray jobs, marketing campaign phases, MAO directives) into Kubernetes Jobs managed by Volcano PodGroups.
- Provide queue isolation between conversational, background, and batch analytics workloads.
- Maintain Temporal as the control-plane while Volcano enforces resource guarantees and prioritisation.
- Instrument scheduling decisions for operators (Prometheus + Grafana) and expose toggles via configuration/feature flags.

## 3. Non-Goals

- Cross-cluster federation of Volcano queues.
- Automatic Ray cluster lifecycle management (manual for v1).
- Replacing Temporal with Volcano (Temporal remains workflow orchestrator).

---

## 4. Current State Summary

- Temporal workers execute all activities inside service pods; no Kubernetes Jobs submitted today.
- Prometheus scrapes orchestrator, MAO, and Temporal metrics; no scheduler telemetry for queues or PodGroups.
- Helm/k8s overlays lack queue definitions or admission controllers beyond default scheduler.
- Ray runs embedded within orchestrator pods (`ray.init(address="auto")`).

---

## 5. Target Design

### 5.1 Workload Classes → Volcano Queues

| Queue | Workloads | SLA Target | Resources | Notes |
|-------|-----------|------------|-----------|-------|
| `interactive` | Session start, MAO directives, unified multi-agent dispatch | p95 < 2 min | Guaranteed CPU 8, Mem 16 Gi | Highest priority; seeded in sandbox via `infra/k8s/local/volcano/queues.yaml`. |
| `batch` | Marketing campaign phases (content, design, analytics) | Completion < 30 min | Guaranteed CPU 16, Mem 32 Gi, burst allowed | Supports gang scheduling; same manifest reserves extra headroom for load tests. |
| `analytics` | Future data/ML training tasks | Throughput oriented | Guaranteed CPU 32, Mem 64 Gi, optional GPU | Disabled by default; defined now for validation pipelines. |

### 5.2 PodGroup Strategy

- Each Temporal activity transitioning to Kubernetes Job emits `volcano.sh/queue-name` and `scheduling.k8s.io/group-name` annotations.
- Min gang size derives from activity payload:
  - Session workflows → 1 (single pod jobs) but still PodGroup for priority control.
  - Marketing distribution → 3 (content, design, analytics workers).
  - MAO directives → N = number of agents invoked in parallel.
- Jobs submitted via new orchestrator module (`services/orchestrator/app/workflows/volcano_launcher.py`).

### 5.3 Control Plane Changes

- Feature flag `ENABLE_VOLCANO_SCHEDULER` toggles new submission path.
- Temporal activities publish job status back via Kubernetes API watch; fallback to inline execution when Volcano disabled.
- Admission webhook policies enforce namespace/resource limits.
- Sandbox provisioning automated via `scripts/volcano/bootstrap-kind.sh` for developer validation.
- Sample PodGroup + job manifest (`infra/k8s/local/volcano/sample-session-job.yaml`) demonstrates minimum viable integration.
- Python helper `services/orchestrator/app/workflows/volcano_launcher.py` wraps kubectl for early-stage submissions.

### 5.4 Observability

- Deploy Volcano metrics ServiceMonitor (`volcano-system` namespace).
- Extend Grafana with queue depth, pending duration, and preemption count panels.
- Emit structured logs from orchestrator when PodGroup events change state.
- Capture pre/post rollout metrics following `baseline-metrics.md` to validate improvements.

---

## 6. Component Diagram

*(Future work: add PlantUML sequence showing Temporal → Volcano → Worker pods → Temporal completion.)*

---

## 7. Rollout Plan Highlights

1. Ship dormant module with feature flag off.
2. Enable in sandbox kind cluster; run synthetic workload suite.
3. Gradually migrate marketing + MAO directives in staging.
4. Expand to session workflow once telemetry meets SLA.

---

## 8. Open Questions

1. What is the minimal set of activities to externalise for initial value?
2. Do we require GPU-aware scheduling in phase 1 (e.g., for future fine-tuning jobs)?
3. How do we backoff/timeout PodGroups when human approval pauses marketing workflows?

---

## 9. Next Steps

- Finalise requirements brief (Sprint 0).
- Implement prototype job launcher for Volcano submissions (in progress).
- Queue manifests committed for sandbox validation (`infra/k8s/local/volcano/queues.yaml`).
- Helper scripts and launcher module scaffolded; awaiting workflow wiring & tests.
- Capture metrics baselines for orchestrator and marketing workloads pre-change.

---

*Add comments and proposed edits via PR; update status once design is ratified.*
