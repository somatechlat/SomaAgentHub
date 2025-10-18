# SomaAgentHub Documentation Style Guide

**Standard Operating Procedure (SOP) for creating, maintaining, and publishing the SomaAgentHub documentation suite.**

---

## 1. Scope & Audience

| Audience | What they need from the docs | How this template helps them |
|----------|-----------------------------|------------------------------|
| New engineers / interns | Quick onboarding, local dev setup, architecture | Provides a **Quick‑Start** guide, architecture overview, and glossary. |
| Platform & SRE teams | Runbooks, incident response, SLO/SLA monitoring | Supplies **Process / System docs** (runbooks, security, observability). |
| Product & Delivery leads | Release checklists, rollback procedures, compliance evidence | Gives **Release & Change‑Management** documentation. |
| External partners / auditors | Compliance evidence, security controls, data‑classification | Delivers **Security & Compliance** docs, change logs, audit trails. |
| Automation bots (CI/CD, doc generators) | Structured source files, predictable naming, machine‑readable metadata | Enforces **file layout, naming conventions, CI linting, auto‑generation hooks**. |

---

## 2. The Four Core Manuals

All documentation should be organized into four primary manuals, each serving a distinct audience. This structure ensures that every stakeholder—user, operator, developer, or new team member—can find the information they need efficiently.

| Manual | Audience | Purpose | File Location (Root) |
|---|---|---|---|
| **User Manual** | End-Users, Product Managers | Explains how to *use* the software to accomplish tasks. | `docs/user-manual/` |
| **Technical Manual** | System Administrators, SREs, DevOps | Explains how to *deploy, operate, and manage* the system. | `docs/technical-manual/` |
| **Development Manual** | Software Engineers, Contributors | Explains how to *build, modify, and contribute* to the codebase. | `docs/development-manual/` |
| **Onboarding Manual** | Agent Coders, New Team Members | Explains how to *quickly become productive* on the project. | `docs/onboarding-manual/` |

---

## 3. File‑Structure & Naming Conventions

### Naming Rules

| Rule | Example | Rationale |
|------|---------|-----------|
| **kebab‑case** for file names | `gateway-api.md` | URL‑friendly, deterministic. |
| **singular** for directories | `runbooks/` | Keeps path depth shallow. |
| **prefixes** for related groups | `incidents/`, `troubleshooting/` | Logical grouping for search. |
| **Versioned files** use `vX.Y.Z` suffix only for release notes | `v1.2.3.md` | Allows chronological sorting. |
| **Diagrams** stored as source (`.puml`, `.drawio`) and rendered PNG via CI | `component-diagram.puml` | Source‑driven, reproducible graphics. |

---

## 4. Content Standards

### Writing Style
- **Active voice**: "The orchestrator manages workflows" not "Workflows are managed by the orchestrator"
- **Present tense**: "The service starts" not "The service will start"
- **Concise**: One idea per sentence, eliminate unnecessary words
- **Technical precision**: Use exact service names, port numbers, and commands

### Code Formatting
- **Inline code**: Use backticks for `service names`, `file paths`, `commands`
- **Code blocks**: Use fenced blocks with language specification
- **Environment variables**: Format as `VARIABLE_NAME`
- **URLs**: Use full URLs for external links, relative paths for internal

### Terminology Consistency
- **SomaAgentHub**: The platform name (not "Soma Agent Hub" or "soma-agent-hub")
- **Gateway API**: The service name (not "gateway" or "API gateway")
- **Orchestrator**: The service name (not "orchestration service")
- **Temporal**: The workflow engine (not "temporal")
- **Kubernetes**: The container platform (not "K8s" in formal docs)

---

## 5. Review, Approval & Maintenance Process

1. **Pull‑Request (PR) Workflow**
   - Docs‑only PR must have the label `documentation`.
   - At least **one reviewer** from the owning team (e.g., Platform for architecture, SRE for runbooks).
   - CI runs **markdownlint**, **link‑checker**, and **diagram‑render** jobs.
   - PR cannot be merged if any lint error persists.

2. **Quarterly Documentation Audit**
   - Owner runs `scripts/audit-docs.py` which:
     - Checks for stale links.
     - Flags sections not updated in >90days.
     - Generates a **Documentation Health Report** (PDF) posted to `#project-docs`.

3. **Feedback Loop**
   - Add a **"Was this page helpful?"** widget (simple star rating) on the generated site.
   - Export ratings weekly; if <4/5, open a "Doc‑Improvement" ticket.

4. **Retention & Archiving**
   - When a service is **deprecated**, move its runbook to `archive/` and add a deprecation notice in the index.

---

## 6. Check‑list for Every New Documentation Piece

| ✅Item | Description |
|--------|-------------|
| **Purpose statement** | One sentence why the doc exists. |
| **Audience** | Who will read it. |
| **Prerequisites** | Tools or knowledge needed before reading. |
| **Step‑by‑step instructions** | Each command in a fenced code block, with expected output. |
| **Verification** | How to confirm success (e.g., `kubectl get pod …`). |
| **Common errors** | A table of symptoms → fixes. |
| **References** | Links to related docs, diagrams, API specs. |
| **Version badge** | Auto‑generated from git tag. |
| **Metadata front‑matter** | `title`, `nav_order`, `tags`. |
| **Linter pass** | markdownlint CI succeeds. |
| **Link check** | All internal links resolve. |
| **Diagram render** | Any `.puml` or `.drawio` included renders correctly in HTML. |
| **Accessibility** | Alt‑text present, colour contrast OK. |

---

## 7. Automation Hooks

| Hook | Tool | What it does |
|------|------|--------------|
| Diagram renderer | `plantuml-cli` (Docker) | Converts `.puml` → PNG on every commit. |
| Markdown lint | `markdownlint-cli2` (GitHub Action) | Enforces style‑guide rules. |
| Link checker | `remark-validate-links` (GitHub Action) | Fails PR if any dead link. |
| Changelog validator | Custom Python script (`scripts/validate-changelog.py`) | Ensures version bump matches git tag. |
| Search index rebuild | MkDocs‑Material `mkdocs build` | Runs automatically on merge to `main`. |
| Doc health report | `scripts/audit-docs.py` (scheduled GitHub Action) | Generates quarterly PDF. |

---

## 8. SomaAgentHub Specific Terms

| Term | Definition |
|------|------------|
| **Agent Orchestration** | Coordination of multiple AI agents working together on complex tasks |
| **Task Capsule** | Reusable execution bundle containing tools, prompts, and policies |
| **Wizard Flow** | Multi-step guided workflow for complex operations |
| **Session Management** | Stateful conversation and context tracking across agent interactions |
| **Policy Engine** | Rule-based governance and compliance enforcement system |
| **Memory Gateway** | Vector and key-value storage for persistent agent context |
| **Temporal Workflow** | Durable, fault-tolerant workflow execution engine |
| **Volcano Scheduler** | Kubernetes batch job scheduler for resource-intensive workloads |
| **SPIFFE/SPIRE** | Zero-trust identity framework for service authentication |
| **Constitution Service** | Governance framework defining agent behavior rules |

---

## 9. Final Remarks

- **Consistency is the KPI:** Every new doc must pass the *Check‑list* above.
- **Automation over manual:** Use the listed CI jobs to keep the docs *always* in sync with the codebase.
- **Living documentation:** Treat each markdown file as source code – version it, review it, test it.

> **When every team member follows this *Documentation Style Guide*, the entire SomaAgentHub knowledge base will be complete, searchable, up‑to‑date, and auditable – a true "single source of truth" for developers, operators, auditors, and automated tooling.**