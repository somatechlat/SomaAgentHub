# SomaAgentHub Project Planner & Wizard Architecture

**Version:** 0.1.0  
**Last Updated:** October 5, 2025  
**Status:** Draft (implementation in progress)

---

## 1. Overview

The Project Planner extends the Orchestrator so agents can translate natural language requests (e.g., "Create a WordPress campaign site") into actionable automation plans. The planner introduces an LLM-driven reasoning layer, a metadata-driven wizard system, and a formal approval gate before any infrastructure or services are provisioned.

### Goals

- Accept free-form project intents and produce structured `ProjectPlan` objects.  
- Guide users through optional wizards that collect only the parameters required for each module (e.g., WordPress deployment, theme configuration).  
- Surface tool recommendations and OSS fallbacks by inspecting the Tool Registry and credential store.  
- Require explicit approval before triggering Temporal workflows that execute capsules and provisioning tasks.  
- Persist plans, answers, and execution outcomes for auditing and continuous learning.

### Non-Goals

- Replacing Temporal or existing automation flows. The planner sits in front of existing execution engines.  
- Hard-coding every wizard flow. All question sets are metadata-driven so operators can add/edit modules without code changes.

---

## 2. High-Level Architecture

```
User Request ─▶ Planner Service (LLM) ─▶ Project Plan Repository ─▶ Approval Gate ─▶ Temporal `project.launch`
                 │                          ▲     │                           │
                 └─▶ Wizard/Manual Intake ──┘     └─▶ Tool Suggestion Layer ──┘
```

1. **Planner Service** ingests the raw prompt, merges tenant context, tool availability, and relevant memory. It runs an LLM prompt to generate a draft plan (objectives, modules, risks) and selects the best capsule blueprint.  
2. **Wizard/Manual Intake** uses the capsule's `intake_schema` to prompt for missing parameters. Users can opt to skip the wizard and select modules/tools manually; dependency rules still apply.  
3. **Project Plan Repository** stores the evolving plan, module states, tool bindings, and provisioning tasks. Each change is versioned and auditable.  
4. **Approval Gate** provides a summary and requires explicit confirmation (with policy headers) before any automation is executed.  
5. **Temporal Workflows** receive the plan payload and orchestrate capsules (e.g., WordPress provisioning, repo scaffolding, QA) using existing services.

---

## 3. Planner Service Design

### 3.1 Components

| Component | Responsibility | Implementation Notes |
|-----------|----------------|----------------------|
| `planner/client.py` | LLM invocation, retries, telemetry | Uses SLM Service (Ray/vLLM) or external provider. Supports streaming/offline modes. |
| `planner/planner_service.py` | High-level orchestration | Collects context (memory, tools), formats prompt, parses LLM output, and persists draft plan. |
| `planner/schemas.py` | Typed data models | Pydantic models for `ProjectPlan`, `ModuleSpec`, `ToolBinding`, `Risk`, `WizardStep`. |
| `planner/prompt_templates/` | Prompt definitions | YAML files referencing capsules and org guidelines. |

### 3.2 Inputs to the Planner

- User prompt and metadata (tenant, session, persona).  
- Capsule catalog metadata (module requirements, dependencies).  
- Tool availability snapshot (adapters + credential status).  
- Memory Gateway entries (past projects, preferences, policies).  
- Tenant configuration (default regions, compliance requirements).

### 3.3 Planner Output

```json
{
  "plan_id": "plan-123",
  "capsule": "website_build_v1",
  "objective": "Launch Fall Promo WordPress site",
  "modules": [
    {"id": "wordpress_deploy", "status": "pending", "dependencies": ["kubernetes_cluster"], ...},
    {"id": "wordpress_theme", "status": "blocked", "depends_on": ["wordpress_deploy"], ...}
  ],
  "tool_suggestions": [
    {"type": "cms", "preferred": "wordpress", "alternatives": ["ghost"]}
  ],
  "risks": ["Provisioning window overlaps maintenance"],
  "questions": [
    {"module": "wordpress_deploy", "question_id": "hosting_target", "prompt": "Where should WordPress run?"}
  ]
}
```

---

## 4. Wizard & Manual Intake Engine

### 4.1 Schema-Driven Wizards

Each capsule defines modules in metadata:

```yaml
modules:
  - id: wordpress_deploy
    title: WordPress Deployment
    questions:
      - id: hosting_target
        prompt: "Where should WordPress run?"
        type: select
        options: ["kubernetes", "local_docker", "managed" ]
        default: "kubernetes"
      - id: site_title
        prompt: "What is the public site title?"
        type: text
      - id: admin_email
        prompt: "Admin email for notifications?"
        type: email
    provisioning_capsule: wordpress_provision_v1
```

### 4.2 Flow

1. Intake manager loads module questions in dependency order.  
2. For each question, it attempts to auto-fill using tenant defaults or previous answers.  
3. Presents question via chat (or modal) with quick replies where appropriate.  
4. Validates answer; if invalid, prompts again.  
5. Upon module completion, stores parameters and advances to the next module.  
6. Users can switch to manual mode, directly choosing modules/tools; dependency validation still enforced.

### 4.3 Module Lifecycle

| State | Description | Trigger |
|-------|-------------|---------|
| `pending` | Module identified but not started | Planner output |
| `in_progress` | Wizard/manual intake collecting answers | Intake manager |
| `review` | Awaiting user confirmation for module summary | Intake manager |
| `approved` | Module ready for execution | User confirmation / plan approval |
| `executing` | Temporal workflow running | `project.launch` workflow |
| `completed` | Execution success | Workflow response |
| `failed` | Execution error | Workflow error handling |

---

## 5. Project Plan Repository

### 5.1 Storage

- **Postgres** (orchestrator DB) for durable records: plans, modules, answers, tool bindings, provisioning tasks, audit events.  
- **Memory Gateway** for conversational snippets, embeddings, and lessons learned (used for future planning prompts).

### 5.2 Key Tables (conceptual)

| Table | Purpose |
|-------|---------|
| `project_plans` | High-level plan metadata (tenant, status, capsule, timestamps). |
| `project_plan_revisions` | Versioned snapshots of plan JSON for audit. |
| `project_plan_modules` | Module states, dependencies, execution links. |
| `project_plan_answers` | Key/value store of wizard responses. |
| `project_plan_tool_bindings` | Selected tools + credential references. |
| `project_plan_tasks` | Provisioning tasks to trigger (capsule IDs, status). |
| `project_plan_events` | Timeline of changes (creation, approval, execution, completion). |

---

## 6. API Surface (new endpoints)

| Method & Path | Description | Status |
|---------------|-------------|--------|
| `POST /v1/projects/analyze` | Run planner on a new prompt; returns draft plan + next steps. | ✳︎ Stub in progress |
| `POST /v1/projects/{plan_id}/intake` | Submit wizard/manual answers; returns next question or summary. | ✳︎ Stub in progress |
| `POST /v1/projects/{plan_id}/approve` | Approve plan for execution; triggers Temporal workflow. | ✳︎ Stub in progress |
| `GET /v1/projects/{plan_id}` | Fetch plan status, module states, execution progress. | ✳︎ Planned |

(✳︎ indicates new endpoints to implement.)

---

## 7. Temporal Workflow Additions

- `project_launch_workflow`: consumes approved `ProjectPlan`, spawns provisioning and coordination activities.  
- Activities for WordPress provisioning, theme configuration, repo scaffolding, QA, analytics wiring.  
- Emits progress events to Kafka and updates plan repository.  
- Handles retries and exposes manual intervention hooks when failures occur.

---

## 8. Implementation Phases

1. **Phase 0 – Planner Foundation**  
   - Create planner package, prompt templates, schemas, and repository layer.  
   - Stub API endpoints that call planner and store results.  

2. **Phase 1 – Wizard Engine**  
   - Build intake manager, question rendering, manual mode, dependency validation.  
   - Integrate with project plan repository and API endpoints.  

3. **Phase 2 – WordPress Example**  
   - Implement WordPress adapter, provisioning capsule, theme module metadata.  
   - Create `website_build_v1` capsule metadata and tests.  

4. **Phase 3 – Execution Wiring & Observability**  
   - Implement `project_launch_workflow`, progress events, dashboards, runbooks.  
   - Add approval policy integration and audit logging.  

5. **Phase 4 – Expansion**  
   - Replicate blueprint approach for other major project types (marketing campaign, onboarding, multi-agent research).  
   - Feed outcomes back into planner prompts for continual improvement.

---

## 9. Next Steps Checklist

- [ ] Scaffold planner, intake, and repository packages inside orchestrator service.  
- [ ] Define capsule metadata extensions (`intake_schema`, `module_dependencies`, `tool_preferences`).  
- [ ] Draft WordPress blueprint and provisioning capsule spec.  
- [ ] Implement API stubs (`projects.py`) with structured TODOs.  
- [ ] Design Temporal workflow skeleton for `project_launch_workflow`.  
- [ ] Update onboarding docs to reference the planner and wizard flow.

---

## 10. References

- `services/orchestrator/app/api/routes.py` – existing session and MAO endpoints.  
- `services/orchestrator/workflows/` – Temporal workflows to integrate with `project.launch`.  
- `services/tool-service/tool_registry.py` – source of tool capability metadata.  
- `docs/SOMAAGENTHUB_USE_CASES.md` – Sample scenarios to encode as capsules.  
- `docs/SomaGent_Platform_Architecture.md` – System overview and existing integrations.

---

*Prepared by:* Orchestrator & Automation Team  
*Reviewers:* Platform Architecture, Product Automation, Governance & Compliance
