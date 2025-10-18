# Volcano Integration Daily Journal

**Purpose:** Provide a rolling log of progress, blockers, and decisions for the Volcano integration effort.

**Audience:** Project contributors, leads reviewing status updates.

**Last Updated:** 2025-10-17

---

## How to Use This Journal

1. Add a new entry at the top of the log for each working day.
2. Include status, next actions, blockers, and links to artifacts (PRs, dashboards, incidents).
3. Keep entries concise but specific enough to help someone resume work after an interruption.

### Entry Template

```
## YYYY-MM-DD

**Focus:**
- 

**Progress:**
- 

**Blockers / Risks:**
- 

**Next Steps:**
- 

**Links:**
- 
```

---

## Journal

## 2025-10-17 (Sprint 3 – observability & policy)

**Focus:**
- Wire production-grade observability and compliance hooks for Volcano scheduling.

**Progress:**
- Added Prometheus `volcano-control-plane` scrape and ServiceMonitors for scheduler/controller pods (`infra/monitoring/prometheus.yml`, `k8s/monitoring/servicemonitors.yaml`).
- Published Grafana dashboard **Volcano Scheduler Operations** covering queue depth, latency, and preemption metrics (`infra/monitoring/grafana/dashboards/volcano-operations.json`).
- Introduced Volcano-specific alert rules (backlog, latency, preemption) and extended runbook guidance for on-call usage (`infra/monitoring/alerting-rules.yml`, `docs/technical-manual/runbooks/volcano-operations.md`).
- Enriched audit events with Volcano job metadata to satisfy compliance requirements (`services/orchestrator/app/workflows/session.py`).

**Blockers / Risks:**
- Need to validate ServiceMonitor label selectors against production chart overrides during next staging deploy.

**Next Steps:**
- Feed Volcano metrics into existing capacity reports and baseline dashboards.
- Capture synthetic alert fire/drill evidence for release readiness review.

**Links:**
- `infra/monitoring/prometheus.yml`
- `k8s/monitoring/servicemonitors.yaml`
- `infra/monitoring/grafana/dashboards/volcano-operations.json`
- `infra/monitoring/alerting-rules.yml`
- `services/orchestrator/app/workflows/session.py`

## 2025-10-17 (Sprint 2 – integration coverage)

**Focus:**
- Validate end-to-end Volcano submission path with real cluster automation.

**Progress:**
- Added `tests/integration/volcano/test_volcano_launcher_e2e.py` to submit jobs via `VolcanoJobLauncher` against a live kind + Volcano sandbox.
- Introduced shared sandbox fixture that provisions queues via `infra/k8s/local/volcano/queues.yaml` and waits for readiness.
- Updated `.github/workflows/ci-volcano.yml` to install dev dependencies and execute the new integration suite alongside the smoke script.

**Blockers / Risks:**
- End-to-end tests require self-hosted runner with `kind`, `kubectl`, and `helm`; need to ensure the runner pool stays healthy.

**Next Steps:**
- Extend coverage to Temporal session workflow path once staging metrics are available.
- Capture job runtime metrics from CI runs and roll them into baseline dashboards.

**Links:**
- `tests/integration/volcano/test_volcano_launcher_e2e.py`
- `.github/workflows/ci-volcano.yml`
- `tests/integration/volcano/conftest.py`

## 2025-10-17 (Sprint 1 – tooling pass)

**Focus:**
- Automate sandbox validation and spike orchestrator integration hooks.

**Progress:**
- Added `run-sample-session.sh` and `cleanup-sample.sh` scripts to automate queue seeding, job submission, artifact capture, and teardown.
- Introduced `VolcanoJobLauncher` utilities plus the `launch-volcano-session-job` activity gated behind `ENABLE_VOLCANO_SCHEDULER`.
- Extended orchestrator configuration and `.env.template` with Volcano defaults (queue, namespace, resource sizing).
- Updated documentation (scheduler guide, runbook, roadmap, metrics plan) to reference the new scripts and workflows.

**Blockers / Risks:**
- Need integration tests once the launcher is wired into real workflows.

**Next Steps:**
- Wire the new activity into the session workflow path when feature flag flips on.
- Capture metrics via the new script and feed into baseline dashboards.

**Links:**
- `services/orchestrator/app/workflows/volcano_launcher.py`
- `scripts/volcano/`

## 2025-10-17 (Sprint 1 Kickoff)

**Focus:**
- Bootstrap Volcano sandbox assets and validate queue definitions.

**Progress:**
- Added reusable queue manifest (`infra/k8s/local/volcano/queues.yaml`) with interactive, batch, and analytics capacities.
- Published sample session job (`infra/k8s/local/volcano/sample-session-job.yaml`) to exercise PodGroup admission.
- Updated `volcano-scheduler.md` with step-by-step sandbox commands, including queue seeding and job validation.
- Extended operations runbook with quick command to restore queue configuration during incidents.

**Blockers / Risks:**
- Need automated cleanup script to remove sample jobs after validation.

**Next Steps:**
- Capture job execution metrics and feed into baseline collection plan.
- Draft orchestrator integration spike notes for Sprint 2 planning.

**Links:**
- `infra/k8s/local/volcano/`

## 2025-10-17

**Focus:**
- Kick off Sprint 0 discovery; map current orchestration flows and scheduler touchpoints.

**Progress:**
- Reviewed `services/orchestrator` workflows; confirmed Temporal orchestrates sessions with inline Ray tasks (no external Kubernetes jobs yet).
- Documented marketing and Kamachiq workflows plus Jobs service patterns; updated workload inventory and requirements accordingly.
- Audited monitoring stack (`infra/monitoring`, `k8s/monitoring`) to verify available metrics and identify Volcano observability gaps.
- Created Volcano sandbox bootstrap script (`scripts/volcano/bootstrap-kind.sh`) and accompanying documentation.
- Drafted architecture RFC and baseline metrics plan under `volcano-integration-notes/`.

**Blockers / Risks:**
- Need runtime metrics (concurrency, resource usage) to validate assumptions; data sources not yet identified.

**Next Steps:**
- Inspect additional workflows (`marketing_*`, `graph_execution`) and Ray deployment patterns.
- Inventory infrastructure manifests under `infra/helm/` and `k8s/` for scheduling hooks.

**Links:**
- `docs/development-manual/volcano-integration-notes/requirements.md`

*(Add newer entries above this block.)*
