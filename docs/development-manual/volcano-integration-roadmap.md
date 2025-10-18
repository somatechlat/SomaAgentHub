# Volcano Integration Roadmap

**Purpose:** Preserve the step-by-step plan for introducing Volcano into SomaAgentHub so the team can resume work even after interruptions.

**Audience:** Platform architects, orchestrator developers, SRE partners.

**Last Reviewed:** 2025-10-17

---

## Prerequisites

- Access to the SomaAgentHub repository and architecture docs (`docs/technical-manual/architecture.md`).
- Familiarity with Temporal workflows (`services/orchestrator`).
- Ability to deploy to a sandbox Kubernetes cluster (Kind or equivalent).
- Working knowledge of Volcano concepts (Queues, PodGroups, Jobs, Plugins).

---

## Roadmap Summary

1. Clarify scheduler requirements and inventory current orchestration assumptions.
2. Prototype Volcano inside an isolated sandbox and document deployment steps.
3. Introduce PodGroup-aware job submission into the orchestrator behind a feature flag.
4. Extend observability, policy enforcement, and runbooks for Volcano-managed workloads.
5. Harden the rollout path from staging to production with validation gates and rollback procedures.

---

## Sprint Plan

### Sprint 0 – Discovery & Alignment (1 week)
- Audit orchestration flows within `services/orchestrator`, `services/common`, and Temporal task queues.
- Inventory infrastructure manifests under `infra/k8s/`, `infra/helm/`, and `k8s/`.
- Capture scheduler-related environment variables from `.env.template` and `common/config/settings.py`.
- Produce a baseline requirements brief covering workload patterns, resource envelopes, and SLA/SLO targets.

**Verification:** Requirements brief stored in `docs/development-manual/volcano-integration-notes/requirements.md` and draft architecture RFC (`volcano-integration-notes/architecture-rfc.md`) linked from this roadmap.

### Sprint 1 – Architecture & Sandbox (1-2 weeks)
- Author a Volcano architecture RFC describing queue hierarchy, priority policies, and integration touchpoints with Temporal.
- Stand up a Volcano-enabled kind cluster; automate bootstrap scripts within `scripts/volcano/`.
	- Use `scripts/volcano/bootstrap-kind.sh` as the baseline provisioning script.
- Wire the sandbox validation script into CI via `.github/workflows/ci-volcano.yml` so every change exercises the sample PodGroup/Job.
- Validate CRDs (`PodGroup`, `Queue`, `JobFlow`) and scheduler plugin configuration.
- Document the sandbox deployment process in `docs/technical-manual/volcano-scheduler.md`.
- Draft metric baseline strategy and begin exporting Prometheus/Temporal snapshots (`volcano-integration-notes/baseline-metrics.md`).
	- ✅ Committed sandbox queue definitions (`infra/k8s/local/volcano/queues.yaml`).
	- ✅ Added sample session job (`infra/k8s/local/volcano/sample-session-job.yaml`) to exercise PodGroup admission.
	- ✅ Added helper scripts under `scripts/volcano/` to run and clean up the sample workload.

**Verification:** Successful `kubectl get podgroup` reflecting sample jobs; sandbox instructions peer reviewed; architecture RFC updated with final queue topology.

### Sprint 2 – Platform Hooks (2 weeks)
- Implement a Volcano-aware job launcher module under `services/orchestrator/app/workflows/`.
- Extend config schema to include queue assignment, gang size, and SLA hints; update `.env.template` and respective `settings.py` defaults.
- Add feature flag toggles so operators can swap between native and Volcano scheduling.
- Cover new functionality with integration tests in `tests/integration/volcano/`.

**Verification:** CI passing on new tests; feature flag documented in deployment notes.

### Sprint 3 – Observability & Policy (1 week)
- Integrate Volcano metrics into existing Prometheus scrape configs (`infra/monitoring/`).
- Extend Grafana dashboards for queue depth, job latency, and preemption counts.
- Capture runbooks for queue saturation, job starvation, and plugin tuning in `docs/technical-manual/runbooks/volcano-operations.md`.
- Ensure auditing hooks capture scheduling decisions for compliance.

**Verification:** Dashboards live in Grafana; runbooks merged; alert rules firing against synthetic load; architecture RFC marked accepted.

### Sprint 4 – Stabilization & Rollout (2 weeks)
- Execute load, chaos, and failover tests via `scripts/load_testing.py` and Temporal stress suites.
- Document rollback procedures and configuration diffs required to disable Volcano cleanly.
- Roll out to staging behind feature flag, collect telemetry, then promote to production with phased activation.
- Conduct post-rollout review and archive learnings in `docs/development-manual/volcano-integration-notes/retro.md`.

**Verification:** Production acceptance checklist completed; rollback drill performed successfully.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Misaligned resource quotas cause starvation | Use dry-run quotas in sandbox and model workloads before production rollout. |
| Temporal workflow assumptions break with gang scheduling | Add contract tests validating task readiness against queue admission status. |
| Observability gaps hide scheduling regressions | Instrument queue depth and job latency dashboards before enabling Volcano in staging. |
| Operator familiarity lag | Schedule training using the runbooks and record sessions for async consumption. |

---

## Recovery Checklist (If Work Is Interrupted)

1. Re-read this roadmap plus linked artifacts in `docs/development-manual/volcano-integration-notes/`.
2. Confirm feature branch status via `git status` and `git reflog`.
3. Validate sandbox cluster health (`kubectl get nodes/pods -A`).
4. Resume next incomplete sprint milestone; update progress tracker in project management tool.
5. Log a brief status note in `docs/development-manual/volcano-integration-notes/daily-journal.md` (create if missing).

---

## References

- Volcano Docs: https://volcano.dev/docs
- SomaAgentHub Technical Manual (`docs/technical-manual/`)
- Temporal Concepts: https://docs.temporal.io/concepts
- Kubernetes Batch Patterns: https://kubernetes.io/docs/concepts/workloads/controllers/job/
- Architecture RFC: `docs/development-manual/volcano-integration-notes/architecture-rfc.md`

---

*Keep this document updated whenever roadmap status changes. Add links to working notes as new files are created.*
