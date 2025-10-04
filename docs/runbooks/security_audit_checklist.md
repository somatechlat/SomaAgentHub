⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Security Audit Checklist

Use this checklist before an external security audit or compliance assessment.

## Documentation & Policies
- [ ] Latest architecture diagram and data flow diagrams stored in `docs/diagrams/`.
- [ ] Security policies (identity, moderation, residency, incident response) reviewed and approved within last 90 days.
- [ ] Runbooks (`security.md`, `kill_switch.md`, `disaster_recovery.md`, `constitution_update.md`) updated with current contacts and procedures.

## Infrastructure Hardening
- [ ] mTLS certificates rotated and documented; SPIFFE/SPIRE configuration captured.
- [ ] Kubernetes NetworkPolicies enforced (deny by default + service-specific allowances).
- [ ] Gateway and tool-service HPA / autoscaling thresholds validated under load tests.
- [ ] Secrets stored in Vault/KMS with audit trail; no plaintext secrets in repo/config maps.

## Logging & Monitoring
- [ ] Prometheus dashboards cover gateway, SLM, MAO, tool, analytics services; alerts tested.
- [ ] Analytics-service anomaly feed hooked into notification orchestrator.
- [ ] All services emit audit events with tenant + actor metadata.
- [ ] SIEM integration tested (sample logs retrieved).

## Identity & Access
- [ ] Capability-scoped JWTs enforced at gateway; tokens expire within policy window.
- [ ] MFA enrollment tested for operator accounts.
- [ ] Training locks & strike counters validated.

## Marketplace & Capsules
- [ ] Capsule submissions require attestation signatures; compliance linting logs stored.
- [ ] Installation history retrievable per tenant; rollback tested.
- [ ] Billing ledgers exportable and reconciled with analytics-service CSV.

## Privacy & Residency
- [ ] Residency variables (`SOMAGENT_GATEWAY_RESIDENCY_*`) set according to deployment region.
- [ ] Tenant data segregation confirmed (Postgres RLS, SomaBrain namespaces).
- [ ] Data retention policies documented and implemented (memory pruning jobs, logs retention).

## Penetration Tests & Scans
- [ ] Dependency scans (Snyk/Trivy) run on latest RC images.
- [ ] SAST/DAST reports collected and tracked.
- [ ] External penetration test scheduled/completed; findings logged with remediation plan.

## Audit Evidence Package
- [ ] Collect test reports, scan results, runbook acknowledgements.
- [ ] Export analytics & billing CSVs for audit timeframe.
- [ ] Prepare release notes and changelog for auditor review.

Mark all items as complete or document exceptions before the audit start date.
