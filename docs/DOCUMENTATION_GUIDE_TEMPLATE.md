# Documentation Guide Template

*Standard Operating Procedure (SOP) for creating, maintaining, and publishing the [Project Name] documentation suite.*

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

The file structure should be organized around the three core manuals.

```
/docs/
│
├─ user-manual/
│   ├─ index.md                     # Landing page for the User Manual
│   ├─ installation.md
│   ├─ quick-start-tutorial.md
│   ├─ features/
│   │   ├─ feature-a.md
│   │   └─ feature-b.md
│   └─ faq.md
│
├─ technical-manual/
│   ├─ index.md                     # Landing page for the Technical Manual
│   ├─ architecture.md              # High-level system overview (C4)
│   ├─ deployment.md                # Installation and configuration steps
│   ├─ monitoring.md                # Dashboards, alerts, and metrics
│   ├─ runbooks/
│   │   ├─ service-a.md
│   │   └─ ...
│   ├─ backup-and-recovery.md
│   └─ security/
│       ├─ secrets-policy.md
│       └─ rbac-matrix.md
│
├─ development-manual/
│   ├─ index.md                     # Landing page for the Development Manual
│   ├─ local-setup.md               # One-page dev-environment setup
│   ├─ coding-standards.md
│   ├─ testing-guidelines.md
│   ├─ api-reference.md
│   └─ contribution-process.md
│
├─ onboarding-manual/
│   ├─ index.md                     # Welcome & project orientation
│   ├─ project-context.md           # Mission, goals, stakeholders
│   ├─ codebase-walkthrough.md      # Architecture & code organization
│   ├─ environment-setup.md         # Development environment guide
│   ├─ first-contribution.md        # Step-by-step first PR guide
│   ├─ team-collaboration.md        # Communication & processes
│   ├─ domain-knowledge.md          # Business logic & technical deep-dive
│   ├─ resources/
│   │   ├─ useful-links.md
│   │   ├─ troubleshooting.md
│   │   └─ glossary.md
│   └─ checklists/
│       ├─ setup-checklist.md
│       ├─ pre-commit-checklist.md
│       └─ pr-checklist.md
│
├─ style-guide.md                 # Global formatting, terminology, lint rules
├─ changelog.md
└─ glossary.md
```

### Naming Rules

| Rule | Example | Rationale |
|------|---------|-----------|
| **kebab‑case** for file names | `gateway-api.md` | URL‑friendly, deterministic. |
| **singular** for directories | `runbooks/` | Keeps path depth shallow. |
| **prefixes** for related groups | `incidents/`, `troubleshooting/` | Logical grouping for search. |
| **Versioned files** use `vX.Y.Z` suffix only for release notes | `v1.2.3.md` | Allows chronological sorting. |
| **Diagrams** stored as source (`.puml`, `.drawio`) and rendered PNG via CI | `component-diagram.puml` | Source‑driven, reproducible graphics. |

---

## 4. Content Blueprint (What to Write)

This section provides a detailed blueprint for the content of each of the three core manuals.

### 4.1 The User Manual (`docs/user-manual/`)

The User Manual guides end-users on how to use the product effectively. It should be task-oriented and free of technical jargon.

| Section | Content |
|---|---|
| **1. Introduction** | A brief, high-level overview of what the software does and the problems it solves. |
| **2. Installation** | Simple, step-by-step instructions for end-users to install or access the software. |
| **3. Quick-Start Tutorial** | A guided walkthrough of a core workflow to help users achieve their first success quickly. |
| **4. Core Features** | Detailed guides for each major feature, explaining the functionality and use cases. Organize in a `features/` subdirectory. |
| **5. FAQ & Troubleshooting** | A list of frequently asked questions and solutions to common user-facing problems. |

### 4.2 The Technical Manual (`docs/technical-manual/`)

The Technical Manual (also known as an Operations or Administration Manual) provides the information needed to deploy, manage, and maintain the system in a production environment.

| Section | Content |
|---|---|
| **1. System Architecture** | A detailed explanation of the system's components and their interactions. Should include C4 diagrams (`architecture.md`). |
| **2. Deployment** | Comprehensive instructions for deploying the system, including prerequisites, configuration options, and verification steps. |
| **3. Monitoring & Health** | Guidance on monitoring the system's health. Should detail key metrics, logging conventions, and pre-built dashboards (`monitoring.md`). |
| **4. Operational Runbooks** | A collection of step-by-step procedures for handling common operational tasks and alerts. Each major service should have its own runbook (`runbooks/`). |
| **5. Backup & Recovery** | Procedures for backing up system data and recovering from a disaster scenario. |
| **6. Security** | A detailed overview of security procedures, including secrets management, access control (RBAC), and hardening guides (`security/`). |

### 4.3 The Development Manual (`docs/development-manual/`)

The Development Manual (also known as a Contributor Guide) contains all the information an engineer needs to understand, build, and contribute to the codebase.

| Section | Content |
|---|---|
| **1. Local Environment Setup** | A one-page guide to setting up a local development environment, including dependencies, tooling, and IDE configuration (`local-setup.md`). |
| **2. Codebase Overview** | An explanation of the repository structure, key libraries/frameworks, and the overall design philosophy. |
| **3. Coding Standards** | The style guide for writing code (e.g., PEP 8 for Python), including formatting, linting rules, and naming conventions (`coding-standards.md`). |
| **4. API Reference** | Auto-generated or manually written documentation for all public APIs, including endpoints, data models, and authentication. |
| **5. Testing Guidelines** | Instructions on how to write and run tests (unit, integration, e2e). Should cover the testing strategy and frameworks used (`testing-guidelines.md`). |
| **6. Contribution Process** | The end-to-end process for contributing code, from branching strategy and pull requests to code reviews and the definition of done (`contribution-process.md`). |

### 4.4 The Onboarding Manual (`docs/onboarding-manual/`)

The Onboarding Manual is specifically designed for **agent coders, new developers, contractors, and team members** who need to quickly become productive on ANY software project.

| Section | Content |
|---|---|
| **1. Project Context & Mission** | What this project does, why it exists, business goals, and success metrics (`project-context.md`). |
| **2. Codebase Walkthrough** | Repository tour, key files/directories, data flow, and architecture patterns (`codebase-walkthrough.md`). |
| **3. Development Environment Setup** | Step-by-step setup with verification commands and troubleshooting (`environment-setup.md`). |
| **4. First Contribution Guide** | Pick a starter issue, make changes, test, submit PR - complete walkthrough (`first-contribution.md`). |
| **5. Team Collaboration Patterns** | Communication channels, code review process, meeting schedules, escalation paths (`team-collaboration.md`). |
| **6. Domain Knowledge Transfer** | Business logic explanations, key algorithms, data models, and integration points (`domain-knowledge.md`). |
| **7. Resources & Checklists** | Quick reference materials, troubleshooting guides, and step-by-step checklists (`resources/`, `checklists/`). |

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
     - Flags sections not updated in > 90 days.
     - Generates a **Documentation Health Report** (PDF) posted to `#project-docs`.
3. **Feedback Loop**
   - Add a **“Was this page helpful?”** widget (simple star rating) on the generated site.
   - Export ratings weekly; if < 4/5, open a “Doc‑Improvement” ticket.
4. **Retention & Archiving**
   - When a service is **deprecated**, move its runbook to `archive/` and add a deprecation notice in the index.

---

## 6. Check‑list for Every New Documentation Piece
| ✅ Item | Description |
|--------|-------------|
| **Purpose statement** – one sentence why the doc exists. |
| **Audience** – who will read it. |
| **Prerequisites** – tools or knowledge needed before reading. |
| **Step‑by‑step instructions** – each command in a fenced code block, with expected output. |
| **Verification** – how to confirm success (e.g., `kubectl get pod …`). |
| **Common errors** – a table of symptoms → fixes. |
| **References** – links to related docs, diagrams, API specs. |
| **Version badge** – auto‑generated from git tag. |
| **Metadata front‑matter** (optional for MkDocs) – `title`, `nav_order`, `tags`. |
| **Linter pass** – markdownlint CI succeeds. |
| **Link check** – all internal links resolve. |
| **Diagram render** – any `.puml` or `.drawio` included renders correctly in HTML. |
| **Accessibility** – alt‑text present, colour contrast OK. |

---

## 7. Automation Hooks (Optional but Recommended)
| Hook | Tool | What it does |
|------|------|--------------|
| Diagram renderer | `plantuml-cli` (Docker) | Converts `.puml` → PNG on every commit. |
| Markdown lint | `markdownlint-cli2` (GitHub Action) | Enforces style‑guide rules. |
| Link checker | `remark-validate-links` (GitHub Action) | Fails PR if any dead link. |
| Changelog validator | Custom Python script (`scripts/validate-changelog.py`) | Ensures version bump matches git tag. |
| Search index rebuild | MkDocs‑Material `mkdocs build` | Runs automatically on merge to `main`. |
| Doc health report | `scripts/audit-docs.py` (scheduled GitHub Action) | Generates quarterly PDF. |

---

## 8. Glossary of Key Terms (for the template itself)
| Term | Definition |
|------|------------|
| Runbook | Step‑by‑step operational guide for a specific service or incident. |
| Helm Release | The named deployment of a Helm chart into a Kubernetes namespace. |
| Kind | Local Kubernetes cluster tool used for development and CI. |
| SLO | Service‑Level Objective – a measurable performance target. |
| SLA | Service‑Level Agreement – contractual commitment to an SLO. |
| RBAC | Role‑Based Access Control – Kubernetes permission model. |
| Vault | Secrets management system used by [Project Name]. |
| CI | Continuous Integration – automated testing & linting pipeline. |
| MkDocs | Static‑site generator for Markdown documentation. |
| PlantUML | Text‑based diagram language; source kept under version control. |

---

## 9. Final Remarks
- **Consistency is the KPI:** Every new doc must pass the *Check‑list* above.
- **Automation over manual:** Use the listed CI jobs to keep the docs *always* in sync with the codebase.
- **Living documentation:** Treat each markdown file as source code – version it, review it, test it.

> **When every team member follows this *Documentation Guide Template*, the entire [Project Name] knowledge base will be complete, searchable, up‑to‑date, and auditable – a true “single source of truth” for developers, operators, auditors, and automated tooling.**
