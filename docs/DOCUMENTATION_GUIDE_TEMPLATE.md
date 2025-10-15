# Documentation Guide Template

*Standard Operating Procedure (SOP) for creating, maintaining, and publishing the SomaAgentHub documentation suite.*

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

## 2. Documentation Types (Helpjuice taxonomy)

| Type | Why it exists for SomaAgentHub | File location (relative to repo root) | Owner |
|------|--------------------------------|---------------------------------------|-------|
| Project Documentation | Captures design decisions, requirements, high‑level architecture. | `docs/architecture.md`, `docs/requirements.md` | Platform Engineer |
| Product Documentation | End‑user‑focused guides: installation, quick‑start, tutorials. | `docs/quick-start.md`, `docs/tutorials/*.md` | SRE / Docs Lead |
| Process Documentation | Runbooks, SOPs, incident response, release flow. | `docs/runbooks/*.md`, `docs/incidents/*.md`, `docs/release-checklist.md` | SRE Lead |
| System Documentation | Detailed component diagrams, data‑model, service contracts. | `docs/system/*.md`, `docs/system/diagrams/*.puml` | Architecture Team |
| Security Documentation | Secrets handling, RBAC, compliance evidence. | `docs/security/*.md` | Security Officer |
| Support Documentation | FAQ, troubleshooting, known error codes. | `docs/faq.md`, `docs/troubleshooting/*.md` | Support / SRE |
| Change‑Log / Release Notes | Versioned history of code & doc changes. | `CHANGELOG.md`, `docs/release-notes/*.md` | Release Engineer |
| Style Guide | Enforces consistent tone, formatting, terminology. | `docs/style-guide.md` | Docs Lead |
| Accessibility Statement | Guarantees WCAG‑compatible docs. | `docs/accessibility.md` | UX / Docs Lead |
| Metrics & Analytics | Tracks doc usage, feedback loops. | `docs/analytics.md` (optional) | Docs Lead |

---

## 3. File‑Structure & Naming Conventions

```
/docs/
│
├─ architecture.md                # High‑level system overview (C4 diagram)
├─ requirements.md                # Functional & non‑functional requirements
├─ quick-start.md                 # One‑page dev‑environment setup
├─ style-guide.md                 # Formatting, terminology, markdown lint rules
├─ accessibility.md               # Accessibility compliance statement
│
├─ runbooks/
│   ├─ gateway-api.md
│   ├─ orchestrator.md
│   └─ … (one file per micro‑service)
│
├─ incidents/
│   ├─ severity-matrix.md
│   └─ communication‑templates.md
│
├─ security/
│   ├─ secrets-policy.md
│   ├─ rbac-matrix.md
│   └─ compliance.md
│
├─ system/
│   ├─ component‑diagram.puml        # PlantUML source (auto‑rendered)
│   ├─ data‑model.md
│   └─ service‑contracts.md
│
├─ faq.md
├─ troubleshooting/
│   ├─ docker‑build‑fails.md
│   └─ pod‑crash‑loop.md
│
├─ release‑checklist.md
├─ changelog.md
└─ reference‑library.md
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

### 4.1 Architecture Overview (`docs/architecture.md`)
1. Purpose paragraph – why the diagram exists.
2. C4 diagram – top‑level system, container diagram, component diagram.
3. Key interactions – list of external services (ClickHouse, Temporal, Vault).
4. Data‑flow narrative – request path from Gateway → Orchestrator → Policy Engine.
5. Version badge – auto‑generated from latest git tag.
> **How:** Write the diagram in PlantUML, commit the `.puml`. Add a CI step that converts it to PNG and embeds it via `![](system/component-diagram.png)`.

### 4.2 Quick‑Start Guide (`docs/quick-start.md`)
| Section | Content |
|---------|---------|
| Prerequisites | OS, Docker, Kind, `kubectl`, Python 3.13, `make`. |
| Cluster creation | `kind create cluster --name soma-agent-hub --config infra/kind/kind-config.yaml`. |
| Build & load images | `make start-cluster` (explain background mode). |
| Verify | `kubectl get pods -n soma-agent-hub-dev` – all **Running**. |
| Smoke test | `make k8s-smoke TEST_NAMESPACE=soma-agent-hub-dev`. |
| Expected output | Show sample console output (✓ signs). |
| Common pitfalls | Missing `requirements.txt`, stale Docker cache – how to fix. |
> **Why:** Gives a *single‑page* onboarding experience for new developers, reducing onboarding time from days to hours.

### 4.3 Runbooks (`docs/runbooks/service>.md`)
Template (copy‑paste for each service):

```markdown
# Service Name> Runbook

## 1. Overview
- **Purpose:** …
- **Namespace:** `soma-agent-hub-<env>`
- **Helm Release:** `service‑release>`

## 2. Health‑Check
```bash
kubectl get pod -l app=service> -n namespace>
kubectl logs -l app=service> -n namespace> -f
```

## 3. Common Failure Modes
| Symptom | Root Cause | Fix |
|---------|------------|-----|
| CrashLoopBackOff | Missing secret | `kubectl apply -f secret.yaml` |
| OOMKilled | Low memory limit | Increase `resources.limits.memory` in `values.yaml` |

## 4. Restart Procedure
```bash
helm upgrade --reuse-values release> ./infra/helm/service>
```

## 5. Metrics to Watch
- **Prometheus query**: `rate(http_requests_total{app="service>"}[5m])`
- **Alert**: `SLA‑<service>-high‑latency`

## 6. References
- Link to service API spec (`docs/api/service>.md`)
- Link to architecture diagram (`../architecture.md#<service>`)
```
> **Why:** Gives on‑call engineers a deterministic, copy‑pasteable set of steps.

### 4.4 Security Controls (`docs/security/*`)
- **Secrets Policy** – list of all secret paths in Vault, rotation schedule, encryption at rest.
- **RBAC Matrix** – table mapping *role → Kubernetes ClusterRole → allowed resources*.
- **Compliance Evidence** – reference to audit logs, retention period, and location of `runbook.md` rotation logs.
> **How:** Use a script (`scripts/generate-rbac-matrix.py`) that reads `infra/terraform/rbac.tf` and outputs a markdown table. Add this script to CI to keep the matrix up‑to‑date.

### 4.5 FAQ & Troubleshooting (`docs/faq.md` + `docs/troubleshooting/*.md`)
- Collect the top 10 tickets from the last sprint.
- For each, write a **Problem → Diagnosis → Fix** block.
- Tag each article with `#docker`, `#k8s`, `#helm` for searchability.
> **Why:** Reduces time‑to‑resolution for repeated issues and feeds the knowledge‑base.

### 4.6 Release Checklist (`docs/release-checklist.md`)
- Keep the **printable table** from the Handbook but add **checkboxes that are auto‑generated** by a CI job (`scripts/generate-release-checklist.py`).
- Include a **link** to the exact git commit that produced the Helm chart (`helm template … > manifest.yaml`).

### 4.7 Style Guide (`docs/style-guide.md`)
| Element | Rule |
|---------|------|
| **Headers** | Use ATX style (`# H1`, `## H2`). Max depth = 4. |
| **Lists** | Use hyphens (`-`) for unordered, numbers for ordered. |
| **Code blocks** | Triple backticks with language tag (`bash`, `yaml`, `python`). |
| **Inline code** | Single backticks, no spaces. |
| **Tables** | Align with `|` and include a header separator line (`---`). |
| **Links** | Prefer relative links (`[Runbook](runbooks/gateway-api.md)`). |
| **Images** | Store source (`.drawio`, `.puml`) in `docs/system/`; embed generated PNG. |
| **Terminology** | Use the **Glossary** terms verbatim; capitalize proper nouns. |
| **Tone** | Direct, imperative for commands; descriptive for concepts. |
| **Accessibility** | Alt‑text for images, avoid all‑caps, use high‑contrast colours in diagrams. |
> Add a **markdownlint** configuration (`.markdownlint.json`) that enforces these rules and run it in CI.

### 4.8 Versioning & Change‑Log (`CHANGELOG.md`)
- Follow **Keep a Changelog** format (## [Unreleased], ## [1.2.3] – YYYY‑MM‑DD).
- Every PR that touches docs must **bump the version** if the change is user‑visible.
- CI job validates that the version in `CHANGELOG.md` matches the most recent git tag.

### 4.9 Publishing & Discoverability
| Step | Command / Action | Purpose |
|------|------------------|---------|
| **Static site generation** | `mkdocs build` (or `docusaurus build`) | Produce HTML docs for internal Confluence or public site. |
| **Search index** | MkDocs‑Material includes full‑text search; ensure `site_dir/search/` is deployed. | Users can find any term in ≤ 2 seconds. |
| **Analytics** | Add a tiny `gtag.js` snippet or `matomo` for page‑view tracking. | Measure which docs are most used, iterate accordingly. |
| **Deploy** | Push built site to `gh‑pages` branch or internal docs server. | Docs always reflect latest `main`/`soma_integration`. |
| **Notification** | On merge, bot posts “📚 New docs released – see link>”. | Keeps team aware of updates. |

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
     - Generates a **Documentation Health Report** (PDF) posted to `#soma-docs`.
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
| Vault | Secrets management system used by SomaAgentHub. |
| CI | Continuous Integration – automated testing & linting pipeline. |
| MkDocs | Static‑site generator for Markdown documentation. |
| PlantUML | Text‑based diagram language; source kept under version control. |

---

## 9. Final Remarks
- **Consistency is the KPI:** Every new doc must pass the *Check‑list* above.
- **Automation over manual:** Use the listed CI jobs to keep the docs *always* in sync with the codebase.
- **Living documentation:** Treat each markdown file as source code – version it, review it, test it.

> **When every team member follows this *Documentation Guide Template*, the entire SomaAgentHub knowledge base will be complete, searchable, up‑to‑date, and auditable – a true “single source of truth” for developers, operators, auditors, and automated tooling.**
