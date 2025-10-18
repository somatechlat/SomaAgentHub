# Volcano Integration Daily Journal

**Purpose:** Provide a rolling log of progress, blockers, and decisions for the Volcano integration effort.

**Audience:** Project contributors, leads reviewing status updates.

**Last Updated:** 2025-10-18

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

## 2025-10-18 (Sprint 1 – CI automation)

**Focus:**
- Automate Volcano sandbox validation inside GitHub Actions and harden helper scripts.

**Progress:**
- Added `CI Volcano Sandbox` workflow that provisions kind, installs Volcano, runs the sample session job, archives artifacts, and tears everything down automatically.
- Updated `run-sample-session.sh` to create the target namespace when missing and ensured every kubectl invocation in CI selects the correct context.
- Harmonised script logging prefixes and post-install guidance in `bootstrap-kind.sh`/`cleanup-sample.sh` so CI output maps cleanly to runbook steps.

**Blockers / Risks:**
- Workflow duration may increase overall CI wall-clock time; need follow-up metrics once it runs routinely.

**Next Steps:**
- Fold workflow status into dashboards and alert on failures affecting Volcano readiness.
- Evaluate extending smoke to run orchestrator job submission once feature flag enables live integration tests.

**Links:**
- `.github/workflows/ci-volcano.yml`
- `scripts/volcano/run-sample-session.sh`

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
