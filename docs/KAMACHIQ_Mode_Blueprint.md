# KAMACHIQ Mode Blueprint

KAMACHIQ Mode (named after the Quechua word for coordinator/guide) orchestrates fully autonomous project delivery: operators describe desired outcomes and SomaStack provisions workspaces, personas, toolchains, and governance hooks automatically. This blueprint summarises required components and interfaces for Sprint 10 completion.

## 1. High-Level Flow
1. **Intent Intake** – Operator issues a high-level command with supporting artefacts (roadmap, requirements). Gateway tags request with tenant/residency metadata.
2. **Planner Capsule** – Analytics + MAO invoke `kamachiq_project_planner` capsule, which:
   - Parses inputs using SLM summariser.
   - Generates deliverable DAG (workstreams, dependencies, budgets).
   - Selects personas/toolkits per node.
3. **Self-Provisioning** – Planner triggers provisioning script:
   - Creates Git repos, Plane boards, CI pipelines.
   - Allocates VSCode.dev containers via Workspace Manager.
   - Seeds SomaBrain memory snapshots.
4. **Execution** – MAO instantiates child capsules (dev, QA, docs) in parallel, abiding by budgets + policy engine gates.
5. **Governance Overlay** – Policy engine enforces domain constitution and budget; governance capsule reviews key artefacts before promotion.
6. **Completion** – Analytics-service records capsule outcomes, governance report generated, release notes drafted automatically.

## 2. Core Components
- **Planner Capsule (`kamachiq_project_planner`)** – YAML template stored in `services/task-capsule-repo/app/capsules/kamachiq_project_planner.yaml` with parameters for project metadata, budgets, milestones.
- **Provisioning Harness (`scripts/kamachiq/provision_stack.sh`)** – Automates repo/tool creation with dry-run mode and delegates to tool-service `/v1/provision`.
  - Env/flags support specifying `TOOL_SERVICE_URL`; when `--execute` is passed, the script calls tool-service with persona/region metadata.
- **Tool Service Provisioning API** – `POST /v1/provision` accepts deliverable provisioning actions and returns simulated job IDs (ready to wire into real adapters).
- **Governance Overlay Capsule (`kamachiq_governance_review`)** – YAML at `services/task-capsule-repo/app/capsules/kamachiq_governance_review.yaml`; ensures compliance checkpoints, collects audit artefacts for launch readiness.
- **MAO Enhancements** – Support nested capsule orchestration, schedule follow-up tasks, broadcast progress events to notification orchestrator.
- **Analytics Hooks** – Track KAMACHIQ runs via `/v1/kamachiq/runs`, produce governance reports summarising DAG, cost, outcomes, and log blocked deliverables.
- **Policy Engine Guardrails** – MAO calls `policy-engine /v1/evaluate` before provisioning; blocked deliverables remain in “blocked” status until manual review.
- **Requeue Store** – Blocked deliverables are recorded for later re-evaluation (`services/mao/app/core/requeue.py`), exposed via MAO `/v1/kamachiq/requeue`, and surfaced via analytics notifications.
- **Policy Re-evaluation** – `POST /v1/kamachiq/requeue/{id}/resolve` re-runs policy-engine checks (or accepts `allow=true` for overrides) before reprovisioning.
- **Auto-Retry Loop** – MAO background task periodically drains the requeue store, rechecking policy and reprovisioning automatically; analytics records `kamachiq_runs` and sends notifications when retries execute.

## 3. Data Contracts
- **Planner Output**:
  ```json
  {
    "deliverables": [
      {
        "id": "api-svc",
        "persona": "developer_backend.v2",
        "tools": ["github", "plane"],
        "budget_tokens": 25000,
        "dependencies": []
      }
    ]
  }
  ```
- **Provisioning Input**: Accepts deliverables JSON, region, tenant, secret references.
- **Governance Report**: One record per KAMACHIQ run stored via analytics-service `/v1/governance/reports`.
- **MAO Plan Execution**: `POST /v1/plans/execute` accepts planner output and spins up deliverable workflows.

## 4. Automation Checklist
- [x] Implement planner capsule YAML and register in capsule repo.
- [x] Extend MAO API with `/templates/{id}/instantiate` usage for planner output.
- [x] Implement provisioning script (CLI + dry-run); integrate with tool-service adapters (next: real integrations).
- [x] Add governance overlay capsule and tie to policy engine thresholds (policy hook pending implementation).
- [x] Record blocked deliverables for requeue + analytics notifications.
- [x] Update analytics dashboards to tag KAMACHIQ runs and show KPI (tokens, success rate, handoffs avoided) via `/v1/kamachiq/summary` and `/v1/kamachiq/runs`.

## 5. Observability & Safety
- Enforce residency/environment variables (region overlays) during provisioning.
- Policy engine must approve each automation step (score ≥ threshold).
- Add new Prometheus metrics: `kamachiq_runs_total`, `kamachiq_run_duration_seconds`, `kamachiq_governance_block_total`.
- Notification orchestrator pushes stage updates, approval requests, final summary.

## 6. Next Steps
- Build prototypes for planner + provisioning harness.
- Pilot KAMACHIQ run on staging project backlog.
- Gather operator feedback; iterate prompts, budget heuristics, governance thresholds.
- Document KAMACHIQ-mode runbook (operations + rollback) once automation is validated.
