# Documentation Archive

**Previous documentation versions and reference materials.**

This directory contains archived documentation that has been superseded by the official manuals but may still be useful for reference.

---

## 📋 Contents

### Phase Implementation Guides (Original)

These documents detail the original 5-phase implementation roadmap for SomaAgentHub. They have been integrated into the main Technical Manual but are preserved here for reference.

| File | Purpose | Status |
|------|---------|--------|
| **PHASE-1-HARDEN-CORE.md** | Vault + Observability stack (Prometheus, Grafana, Loki, Tempo) | ✅ Complete |
| **PHASE-2-ZERO-TRUST.md** | Istio mTLS, OPA/Gatekeeper, SPIRE workload identity | ✅ Complete |
| **PHASE-3-GOVERNANCE.md** | OpenFGA authorization, Argo CD GitOps, Kafka event pipeline | ✅ Complete |
| **PHASE-4-AGENT-INTELLIGENCE.md** | LangGraph multi-agent, semantic RAG, orchestration patterns | ✅ Complete |
| **PHASE-5-OPS-EXCELLENCE.md** | k6 load testing, Chaos Mesh, production hardening | ✅ Complete |

### Roadmap Documents

| File | Purpose | Status |
|------|---------|--------|
| **ROADMAP-2.5-COMPLETE.md** | Executive summary of complete implementation (30,000+ words) | ✅ Reference |
| **ROADMAP-2.5.md** | Original roadmap planning document | 📦 Historical |

---

## 🔗 Where to Find Current Information

**Use the main documentation manuals instead:**

| Topic | Location | Purpose |
|-------|----------|---------|
| **Deployment** | `docs/technical-manual/deployment.md` | Docker Compose & Kubernetes procedures |
| **Architecture** | `docs/technical-manual/architecture.md` | System design & components |
| **Monitoring** | `docs/technical-manual/monitoring.md` | Observability & dashboards |
| **Security** | `docs/technical-manual/security/` | Access control & hardening |
| **Setup** | `docs/onboarding-manual/environment-setup.md` | Production-grade local dev |
| **Development** | `docs/development-manual/` | Code contribution guide |

---

## 📖 How to Use This Archive

### If you need Phase implementation details:

1. Start with the main **Technical Manual** (`docs/technical-manual/`)
2. Check specific sections (e.g., `deployment.md`, `security/`)
3. Refer to archived PHASE documents for implementation context

### If you need historical context:

Read **ROADMAP-2.5-COMPLETE.md** for the original vision and complete implementation summary.

### If you're auditing the project:

All Phase implementations are verified in:
- Kubernetes manifests: `k8s/`
- Infrastructure configs: `infra/`
- Implementation scripts: `scripts/`
- Service code: `services/`

---

## 📝 Notes

- Phase implementations have been completed and committed
- All code is production-ready and deployed via git
- Use active documentation manuals for current procedures
- Archive files are preserved for historical reference only

---

**For current documentation, see [Technical Manual Index](../technical-manual/index.md)**
