SomaAgentHub Roadmap (Canonical)
================================

Use these documents for roadmap status and plans:

- Sprint-Based Roadmap (current): docs/sprint-roadmap.md
- Updated Production Plan (Temporal executor): docs/ROADMAP-2.5.md
- Historical summary (archived): docs/archive/ROADMAP-2.5-COMPLETE.md

The repository tracks the sprint-based roadmap as the primary source of truth.
Archived documents are preserved for context and may overstate completion.

Memory‑as‑a‑Service (MaaS) – Quick Facts
----------------------------------------
- Ports (cluster Services):
  - memory-gateway: 10021 (targets container port 8000)
  - qdrant: 10005 → 6333
  - redis: 10003 → 6379
- Env for memory-gateway (Helm values):
  - `QDRANT_URL: http://qdrant:6333`
  - `REDIS_URL: redis://redis:6379/0`
- Observability:
  - `/metrics` on memory-gateway exports `somabrain_requests_total`, `qdrant_up`, `redis_up`.
  - ServiceMonitors enabled via `serviceMonitors.enabled: true`.
  - Redis exporter is enabled by default; Qdrant ServiceMonitor scrapes `/metrics`.
