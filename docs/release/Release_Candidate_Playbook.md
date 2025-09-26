# Release Candidate Playbook

Use this playbook to promote SomaStack from beta → release candidate → GA. Follow the sequence; do not skip steps.

## 1. Freeze & Prep
- Announce code freeze window in #engineering and #ops.
- Merge only critical fixes behind feature toggles.
- Ensure CHANGELOG is up to date; tag outstanding issues.

## 2. Build Artifacts
1. Run full CI suite (lint, type, unit, contract tests).
2. Build containers for all services with release candidate tag (`rc-<yyyymmdd>-<build>`).
3. Sign container digests (cosign or equivalent) and push to registry.

## 3. Deploy to Staging
- Apply Terraform plan against staging using `infra/terraform` (primary + failover regions).
- Deploy Helm chart with region overlays + KEDA enabled:
  ```bash
  helm upgrade --install somagent-staging infra/k8s/charts/somagent \
    -f infra/k8s/overlays/us-east/values.yaml \
    --set image.tag=rc-20240501-001
  ```
- Verify gateway residency enforcement and tool signature checks.

## 4. Validation Suite
- Run performance profiling: `scripts/perf/profile_gateway.sh https://staging-gateway/v1/status`.
- Execute marketplace regression capsules (capsule install, MAO template import, billing events).
- Run DR drill capsule (`dr_failover_drill`) and ensure analytics `/v1/drills/disaster/summary` reports success.
- Trigger persona regression automation endpoints; confirm notifications arrive.

## 5. Observability Sign-off
- Check Grafana dashboards for both regions (gateway latency, SLM tokens, tool billing).
- Confirm Prometheus federation and Tempo traces show dual-region traffic.
- Analytics exports: capture `GET /v1/exports/capsule-runs?tenant_id=demo`, `GET /v1/exports/billing-ledger?tenant_id=demo` snapshots and archive.

## 6. Security & Compliance
- Review `docs/runbooks/security_audit_checklist.md` items.
- Confirm kill-switch runbook tested within last 90 days.
- Validate tool registry manifests/signatures with `services/tool-service/app/core/security.py` helpers.

## 7. Release Candidate Tagging
- Create Git tag `vX.Y.0-rcN`.
- Publish release notes draft (highlight features, security changes, migration steps).
- Distribute release candidate containers to pilot customers or internal squads.

## 8. Monitoring Window
- Run RC for agreed window (24–72h).
- Track analytics dashboards for anomalies (`/v1/anomalies/scan`).
- Log incidents or fixes; if hotfix required, bump `rcN` tag and repeat validation.

## 9. GA Promotion
Once the monitoring window passes without blockers:
- Retag containers as GA `vX.Y.0` (immutable digests only).
- Update Helm chart values + overlays with GA tag.
- Publish final release notes and update documentation landing page.
- Remove code freeze; open next sprint.

Keep this playbook updated as automation improves (e.g., Temporal pipelines, automated load tests).EOF
