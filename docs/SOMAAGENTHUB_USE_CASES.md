# SomaAgentHub Operational Use Cases

**Version:** 1.0.0  
**Last Updated:** October 5, 2025  
**Audience:** Operators, automation agents, and developers orchestrating end-to-end workflows on SomaAgentHub.

This guide packages ready-to-run scenarios that demonstrate how to combine SomaAgentHub services (Gateway API, Orchestrator, Memory Gateway, Tool Service, Marketplace Capsules, and observability stack) to deliver real outcomes. Each use case lists prerequisites, step-by-step execution, validation checkpoints, and extensibility tips.

> For foundational setup, read [`SOMAAGENTHUB_AGENT_ONBOARDING.md`](./SOMAAGENTHUB_AGENT_ONBOARDING.md). For low-level API references, consult [`SOMAGENTHUB_INTEGRATION_GUIDE.md`](./SOMAGENTHUB_INTEGRATION_GUIDE.md).

---

## Table of Contents

1. [Launch a Multi-Channel Marketing Campaign](#1-launch-a-multi-channel-marketing-campaign)
2. [Ship a Marketing Website](#2-ship-a-marketing-website)
3. [Deliver Weekly Data Insights](#3-deliver-weekly-data-insights)
4. [Run Incident Response & Postmortem](#4-run-incident-response--postmortem)
5. [Automate Employee Onboarding](#5-automate-employee-onboarding)

---

## 1. Launch a Multi-Channel Marketing Campaign

**Goal:** Ideate, produce assets, schedule posts, and track performance across email, blog, and social channels.  
**Primary agent roles:** Strategist, Content Writer, Designer, Distribution Manager.  
**Core services & adapters:** Orchestrator, Tool Service (`notion`, `github`, `slack`, `figma`, `plane`), Memory Gateway, Marketplace capsule `marketing_campaign_v1` (example).

### Prerequisites
- Marketplace capsule created (`services/marketplace/`) describing workflow stages, agent assignments, and SLA metrics.
- Tool credentials: Notion integration token, GitHub PAT, Slack bot token, Figma API key.
- Content repository (GitHub or GitLab) seeded with landing page templates.

### Execution Steps
1. **Kick off workflow**: `POST /v1/workflows/start` with capsule `marketing_campaign_v1`, target launch date, personas, and distribution targets.
2. **Gather research**: Strategist agent invokes Tool Service `notion.search_database` and `plane.create_cycle` to pull backlog context and allocate sprint capacity.
3. **Draft messaging**: Writer agent queries Memory Gateway (`/v1/rag/retrieve`) for brand voice, then calls `/v1/chat/completions` to generate copy variations.
4. **Design assets**: Designer agent hits `figma.render_component` (custom capability) to duplicate templates, updating color palette and export variants.
5. **Review & approvals**: Orchestrator parallelizes `github.create_pull_request` for blog drafts and `slack.send_message` for stakeholder sign-off. Reviewer agent merges once approvals logged.
6. **Schedule distribution**: Distribution manager uses `github.trigger_workflow` to run email automation pipeline and `slack.schedule_message` (if supported) for community announcement.
7. **Activate analytics**: Register campaign metadata in Memory Gateway for later attribution (e.g., `campaign:2025q4-launch`).

### Validation Checklist
- ✔️ Workflow run status transitions to `completed` with `success=true` payload.  
- ✔️ All Tool Service calls return `200` and persisted assets exist (Figma file links, PR merged).  
- ✔️ Campaign metadata stored via `/v1/remember` and retrievable.  
- ✔️ Observability: Grafana dashboard `Marketing Ops` shows traffic spike once live.

### Extension Ideas
- Add `playwright.automate_workflow` step to smoke-test landing page forms.  
- Pipe real-time performance into Slack using scheduled orchestrator heartbeat.

---

## 2. Ship a Marketing Website

**Goal:** Stand up a new marketing site or microsite, from requirements intake through production deployment.  
**Primary agent roles:** Product Manager, Coder, QA, DevOps.  
**Core services & adapters:** Orchestrator, Tool Service (`github`, `gitlab`, `kubernetes`, `terraform`, `playwright`), Memory Gateway, Observability stack.

### Prerequisites
- Repo access credential (`SOMAAGENT_GIT_TOKEN`) and Kubernetes cluster credentials registered in Vault/Policy Engine.  
- Marketplace capsule `marketing_site_v2` defining stages (discovery → build → QA → deploy).  
- Helm chart or k8s manifests under `infra/k8s/marketing-site/`.

### Execution Steps
1. **Initiate project**: `POST /v1/workflows/start` referencing `marketing_site_v2`, providing site goals and design brief IDs.
2. **Requirement intake**: Product Manager agent retrieves Memory Gateway entries for tone/style; logs decisions back via `/v1/remember`.
3. **Repo scaffolding**: Coder agent calls `github.create_repository` (or `gitlab.create_project`), then commits starter code using `github.create_file` API for CI pipeline.
4. **Implementation**: For each page module, coder agent invokes SLM completions to draft React/Vue components, pushes branches, and opens PRs (`github.create_pull_request`).
5. **Testing**: QA agent triggers `playwright.automate_workflow` running e2e suite from `examples/`. Store reports in MinIO using shared utilities (`services/common/minio_client.py`).
6. **Infrastructure prep**: DevOps agent runs `terraform.plan` then `terraform.apply` to provision CDN or DNS records and leverages `kubernetes.create_deployment` to ship the container.
7. **Go-live**: Execute `helm upgrade --install` via Orchestrator task; verify with `GET http://marketing.example.com/health` and update runbook.
8. **Post-launch monitoring**: Register site in Prometheus using Tool Service `kubernetes.create_service_monitor` (custom capability) and set alerts.

### Validation Checklist
- ✔️ CI pipeline green; `npm run build` artifacts uploaded.  
- ✔️ Deployment pods healthy (`kubectl get pods`).  
- ✔️ Synthetic tests (Playwright) pass; metrics streaming to Grafana.

### Extension Ideas
- Automate Lighthouse performance checks nightly.  
- Add Memory Gateway snapshot of technical debt backlog for next iteration.

---

## 3. Deliver Weekly Data Insights

**Goal:** Produce a recurring analytics packet combining product metrics, revenue, and qualitative notes.  
**Primary agent roles:** Data Analyst, Narrator, Reviewer.  
**Core services & adapters:** Analytics Service (under `services/analytics-service/`), Tool Service (`clickhouse`, `notion`, `slack`, `github`), Memory Gateway, Scheduler (Temporal).

### Prerequisites
- Access to ClickHouse or warehouse credentials (configured via Tool Service adapter).  
- Notion workspace for report publishing.  
- Marketplace capsule `weekly_insights_v1` with cron trigger (e.g., every Monday 09:00 UTC).

### Execution Steps
1. **Schedule workflow**: Register recurring Temporal schedule targeting `weekly_insights_v1` via `POST /v1/workflows/schedules`.
2. **Extract metrics**: Data Analyst agent invokes Tool Service `clickhouse.query` to pull product usage tables; caches raw results in Memory Gateway with TTL.
3. **Generate charts**: Agent uses Analytics Service endpoints (`/v1/analytics/charts`) to render PNG/SVG assets, storing URIs in report context.
4. **Draft narrative**: Narrator agent calls `/v1/chat/completions` with metrics, prior week summary from Memory Gateway, and tone guidelines to produce executive summary.
5. **Compile report**: Use `notion.create_page` to publish, embedding chart URLs. Simultaneously, `github.create_issue` can track follow-up actions.
6. **Stakeholder distribution**: Post highlights in Slack channel via `slack.send_message`, attaching Notion link and key KPIs.

### Validation Checklist
- ✔️ Workflow run logs stored; history accessible via `/v1/workflows/{run_id}`.  
- ✔️ Notion page published with correct metadata.  
- ✔️ Slack notification delivered; Memory Gateway contains archived summary for continuity.

### Extension Ideas
- Add anomaly detection step using SLM to scan metrics.  
- Push CSV extracts to S3 via Tool Service `aws.upload_object` for BI teams.

---

## 4. Run Incident Response & Postmortem

**Goal:** Detect service degradation, coordinate triage, remediate, and document root cause analysis.  
**Primary agent roles:** Incident Commander, Responder, Communications Lead.  
**Core services & adapters:** Monitoring stack (Prometheus/Alertmanager), Tool Service (`slack`, `jira`, `kubernetes`, `confluence`), Orchestrator runbooks, Memory Gateway.

### Prerequisites
- Alertmanager configured to call SomaAgentHub webhook (`/v1/incidents/ingest`).  
- Incident response capsule `prod_incident_v3` with decision tree and escalation policies.  
- Confluence or Notion space for postmortems.

### Execution Steps
1. **Alert ingestion**: Prometheus fires alert → Alertmanager sends payload → Gateway API triggers `prod_incident_v3` workflow.
2. **Context enrichment**: Incident Commander agent queries Memory Gateway for related past incidents and known mitigations.
3. **War room setup**: Tool Service `slack.create_channel` (e.g., `#inc-2025-10-05`) and invites on-call roster using `slack.invite_users`.
4. **Mitigation**: Responder agent executes `kubernetes.rollback_deployment` or `terraform.apply` depending on blast radius; attaches logs to workflow notes.
5. **Status updates**: Communications agent posts updates in stakeholder channel and, if necessary, triggers Statuspage integration via custom adapter.
6. **Resolution**: Once metrics stable, update workflow status to `resolved`, archive Slack channel, and open Jira ticket for follow-up using `jira.create_issue` (type `postmortem`).
7. **Postmortem drafting**: Agent uses `/v1/chat/completions` seeded with incident timeline to draft RCA, publishing via `confluence.create_page`.

### Validation Checklist
- ✔️ Incident workflow closed with resolution summary attached.  
- ✔️ Remediation actions logged in Jira.  
- ✔️ Postmortem document stored and linked in Memory Gateway for future reference.

### Extension Ideas
- Automate severity scoring using historical MTTR data.  
- Integrate PagerDuty OSS alternatives (e.g., Grafana OnCall) for paging.

---

## 5. Automate Employee Onboarding

**Goal:** Provision accounts, deliver training plan, and capture feedback for new hires.  
**Primary agent roles:** HR Coordinator, IT Admin, Mentor.  
**Core services & adapters:** Identity Service, Tool Service (`slack`, `notion`, `github`, `plane`, `aws`), Memory Gateway, Capsule `employee_onboarding_v2`.

### Prerequisites
- HRIS export or CSV with new hire metadata accessible via secure storage.  
- Templates for onboarding tasks in Plane or Jira.  
- Notion workspace with onboarding handbook.

### Execution Steps
1. **Trigger onboarding**: HR coordinator uploads new hire data to Memory Gateway (`/v1/remember`) and starts workflow with hire date, role, manager.
2. **Account provisioning**: IT admin agent uses Identity Service to create service accounts, calls `github.invite_user` and `slack.invite_user`, and provisions AWS IAM roles via `aws.create_iam_user`.
3. **Workspace setup**: Notion adapter clones onboarding workspace, assigns tasks. Plane adapter creates sprint board with week-by-week checklist.
4. **Mentor pairing**: Orchestrator selects mentor (based on Memory Gateway preferences) and schedules intro meeting through Calendar adapter if configured.
5. **Training drip**: Daily tasks triggered using Temporal timers, sending Slack nudges and linking to relevant documentation.
6. **Feedback capture**: After two weeks, workflow invokes `/v1/chat/completions` to craft feedback survey, posts to Slack, and logs responses in Memory Gateway for future iterations.

### Validation Checklist
- ✔️ All account creation calls succeed; auditor agent verifies via `slack.list_users` and `github.list_invitations`.  
- ✔️ Plane/Jira board populated with tasks, due dates set.  
- ✔️ Feedback stored for retro and automatically appended to onboarding knowledge base.

### Extension Ideas
- Introduce gamified learning badges tracked in Memory Gateway.  
- Auto-close workflow after 90-day review meeting.

---

## Next Steps

- Clone these scenarios to Marketplace by exporting capsule definitions under `services/marketplace/`.  
- Augment Tool Service with additional open-source adapters (Mattermost, Gitea, Jenkins) so each workflow has OSS equivalents.  
- Extend `docs/runbooks/` with scenario-specific runbooks referencing this guide.

Report improvements or new use cases to the documentation team via `docs/runbooks/contributions.md`.
