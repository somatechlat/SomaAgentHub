# Hardening Checklist

Last Updated: October 9, 2025

## Reliability
- [ ] Liveness & readiness probes tuned
- [ ] Resource requests/limits set; HPA configured
- [ ] Pod disruption budgets for core services
- [ ] Restart tests pass

## Security
- [ ] Ingress + TLS
- [ ] Auth on protected routes; OpenAPI checks in CI
- [ ] Secrets management (K8s Secrets or external)
- [ ] Image scanning and SBOM

## Observability
- [ ] ServiceMonitors for core services
- [ ] Dashboards for latency, errors, saturation
- [ ] Logs centralized; Loki optional
- [ ] Alerts for SLO breaches

## Data
- [ ] PVCs defined and mounted where needed
- [ ] Backups and restore procedures
- [ ] Migration scripts validated

## Operations
- [ ] Runbooks for incidents and scaling
- [ ] Release automation
- [ ] Chaos experiments scheduled (safe window)
