# KAMACHIQ Operations Runbook

Use this guide to launch and monitor fully automated KAMACHIQ project deliveries.

## 1. Prerequisites
- Planner capsule (`kamachiq_project_planner`) and governance capsule (`kamachiq_governance_review`) installed for the tenant.
- Tool-service adapters signed and available (GitHub, Plane, etc.).
- Policy engine thresholds configured for the tenant (budget, risk).
- Access to analytics-service (`/v1/kamachiq/*`, `/v1/drills/*`).

## 2. Kick Off a Run
1. Import or verify planner template:
   ```bash
   python scripts/ops/schedule_dr_drill.py http://localhost:8200 tenant-a ops-automation --capsule kamachiq_project_planner --cron "0 2 * * 1"
   ```
   (Replace schedule if you prefer ad-hoc runs; you can call `/v1/templates/import` directly.)
2. Execute planner via MAO API:
   ```bash
   curl -X POST http://localhost:8200/v1/plans/execute \
     -H 'Content-Type: application/json' \
     -d @planner-output.json
   ```
3. MAO provisions deliverables, runs governance overlay, and records analytics (`/v1/kamachiq/runs`).

## 3. Monitoring
- **Workflows**: `GET /v1/workflows` for status; use notification orchestrator for event stream.
- **Analytics**: `GET /v1/kamachiq/summary` (overview) and `GET /v1/kamachiq/runs?tenant_id=...` (history).
- **Governance Reports**: `GET /v1/governance/reports?tenant_id=...` for compliance trail.
- **Policy blocks**: `GET /v1/kamachiq/requeue` to inspect blocked deliverables; resolve via `POST /v1/kamachiq/requeue/{id}/resolve`.

## 4. Troubleshooting
- **Provisioning failed**: check tool-service logs; re-run provisioning harness with `--execute` after verifying credentials.
- **Policy blocks never clear**: inspect analytics notifications; adjust policy engine weights or supply override via resolve endpoint.
- **Budget overrun**: analytics billing ledger shows tokens/cost per service.
- **Residency issues**: ensure gateway allow-list includes tenant for current region.

## 5. Post-Run
- Archive governance report and analytics summary to your documentation system.
- Update knowledge base (capsule improvements) if new learnings should feed future planner runs.
- Schedule next run (weekly/biweekly) using MAO template schedule or Temporal workflow.

Keep this runbook updated as KAMACHIQ automation evolves.
