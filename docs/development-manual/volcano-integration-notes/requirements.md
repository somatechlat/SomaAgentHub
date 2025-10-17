# Volcano Integration Requirements Brief

**Purpose:** Capture current-state assumptions and desired capabilities before implementing Volcano.

**Audience:** Platform architects, orchestrator maintainers, SRE reviewers.

**Last Updated:** 2025-10-17

---

## Template Instructions

Fill in each section during Sprint 0 discovery. Update the "Last Updated" field with every change. Remove instructional text when content is finalized.

### 1. Workload Inventory

| Workflow | Current Scheduler Behavior | Peak Concurrency | Resource Profile | SLA/SLO |
|----------|---------------------------|------------------|------------------|---------|
| `session-start-workflow` (Temporal) | Activities run inside orchestrator pod; Ray tasks scheduled via `ray.init(address="auto")` | 20 concurrent sessions per pod (bounded by worker count) | Each Ray task holds ~1 vCPU / 512 MiB for ~1 min | Session completion p95 < 2 min |
| `unified-multi-agent-workflow` | Temporal activities invoking CrewAI/Autogen/LangGraph libraries within worker pod | 10 concurrent per worker | CPU-bound spikes (3–4 vCPU) with bursty memory usage (~1 GiB) | Response p95 < 5 min |
| `multi-agent-orchestration` (MAO) | Sequential directives executed inline; heavy use of SLM completions and notifications | Depends on directives count (typically 3–5) | Sustained SLM requests (~1 CPU per directive) with external HTTP calls | Must complete orchestrations in <10 min |
| `marketing-campaign` | Long-running saga with 6 phases; all activities executed inline via HTTP integrations | 4 concurrent campaigns (approval gates slow throughput) | Mix of I/O heavy HTTP calls + bursts of content generation (up to 2 vCPU, 2 GiB) over 15–25 min | Completion within business day; approval gating manual |
| `kamachiq` project workflows | Temporal orchestrates parallel task waves; activities spawn agents inline | Worker count currently 1–2 per pod | Potentially high parallel fan-out; tasks share orchestrator CPU/memory | Pilot SLA TBD |
| Jobs service background tasks | FastAPI endpoint spawns asyncio background coroutines | Tens of short-lived async jobs | Lightweight CPU usage, relies on Redis pub/sub | Best-effort |

### 2. Scheduler Requirements

- **Must Have:**
	- Gang/PodGroup admission so multi-agent bursts can launch all helper pods together when externalised from the orchestrator.
	- Queue-level quotas to isolate tenant workloads once Ray jobs move to dedicated workers.
	- Preemption policies that honour Temporal retry semantics (avoid duplicate execution).
- **Context:** None of the current workflows submit Kubernetes Jobs; all work executes inside service pods. Volcano adoption assumes refactoring activities (Ray tasks, heavy HTTP fan-out) into dedicated worker pods managed by PodGroups.
- **Should Have:**
	- Elastic resource borrowing between `high-priority` and `standard` queues.
	- SLA plugin to favour short-lived conversational workflows over batch analytics.
	- Native GPU awareness for upcoming model-fine-tuning workloads (roadmap Q4).
- **Won't Have:**
	- Cross-cluster federation in the first release.
	- Automatic scale-out of Ray clusters (remains manual until validated).

### 3. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Temporal retries conflict with PodGroup failures | Workflow stalls or double-executes | Medium | Align retry/backoff settings with Volcano job status events; add circuit breaker activity. |
| Ray workloads still local to orchestrator pod | Resource contention even after Volcano adoption | High | Stage migration of Ray execution to dedicated Volcano-managed workers before enabling feature flag. |
| Queue misconfiguration starves long-running analytics | Missed SLA for marketing workflows | Medium | Model workload categories during Sprint 0; enforce minimum share via queue weights. |
| Marketing workflow approval latency hides resource waste | Idle PodGroups hold slots waiting for human approval | Medium | Split human-in-loop phase into separate queue with timeout-based release hooks. |

### 4. Dependencies

- Infrastructure changes required:
	- Helm overlays for Volcano controllers, ServiceMonitor, and queue CRDs.
	- Feature flag plumbing in orchestrator deployment (`ENABLE_VOLCANO_SCHEDULER`).
	- Prometheus scrape/ServiceMonitor updates so Volcano scheduler and queue metrics land in existing observability stack.
	- Sandbox queue manifests checked into `infra/k8s/local/volcano/` for rapid validation.
	- Helper scripts (`scripts/volcano/run-sample-session.sh`, `scripts/volcano/cleanup-sample.sh`) to automate validation runs.
- Service owners to coordinate with:
	- Orchestrator maintainers (#soma-workflows).
	- Platform SRE (#somagenthub-ops).
	- Data/marketing workflow owners for batch jobs.
	- Kamachiq autonomous team for project orchestration workloads.
- External approvals/compliance checkpoints:
	- Security review for new scheduler admission webhook.
	- Change-management sign-off for production rollout.

### 5. Open Questions

1. Which workloads should migrate first to Volcano-managed PodGroups to deliver immediate impact?
2. Do we need GPU-aware queues in the initial release or can that wait for the analytics sprint?
3. What mechanism will release queued resources when human approval pauses marketing workflows?

---

## Verification Checklist

- [x] Inventory completed for all critical workflows.
- [ ] Requirements reviewed with platform leadership.
- [ ] Risks logged in issue tracker.
- [x] Document linked from `volcano-integration-roadmap.md`.

---

## Observability & Telemetry Sources

- Prometheus scrapes `temporal:9090`, `orchestrator:8001`, `mao-service:8002`, Tool Service, and all monitoring-labeled pods (`infra/monitoring/prometheus.yml`).
- ServiceMonitors exist for orchestrator, gateway, policy, identity, and somallm providers (`k8s/monitoring/servicemonitors.yaml`); extend with Volcano scheduler and queue exporters.
- Temporal workflow histories provide concurrency/backlog metrics—coordinate with Temporal dashboards once scraped metrics are catalogued.
- Ray usage currently local to orchestrator pods; enable Ray metrics endpoints when migrating workloads to dedicated workers.

---

## References

- `docs/technical-manual/architecture.md`
- `docs/technical-manual/volcano-scheduler.md`
- `docs/development-manual/volcano-integration-notes/baseline-metrics.md`
- Volcano official docs: https://volcano.dev/docs
