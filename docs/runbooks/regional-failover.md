# Regional Failover Runbook

## Overview

This runbook provides step-by-step procedures for handling regional failures in the SomaAgent platform.

**Last Updated**: 2025-01-05  
**Maintainer**: Platform Team  
**Severity**: P1 (Critical)

---

## Table of Contents

1. [Detection & Assessment](#detection--assessment)
2. [Failover Procedures](#failover-procedures)
3. [Recovery Procedures](#recovery-procedures)
4. [Rollback](#rollback)
5. [Post-Incident](#post-incident)

---

## Detection & Assessment

### Automated Alerts

Regional failures trigger these alerts:

- **Route53 Health Check Failed** - Regional endpoint unhealthy
- **EKS Cluster Unreachable** - Control plane down
- **RDS Connection Timeout** - Database unavailable
- **High Error Rate** - 5xx errors > 10% for 5 minutes

### Manual Verification

```bash
# Check regional health
curl -f https://api-usw2.somaagent.io/health
curl -f https://api-euw1.somaagent.io/health

# Check Route53 health checks
aws route53 get-health-check-status --health-check-id <HEALTH_CHECK_ID>

# Check EKS cluster status
aws eks describe-cluster --name somaagent-us-west-2 --region us-west-2
aws eks describe-cluster --name somaagent-eu-west-1 --region eu-west-1
```

### Assessment Criteria

Determine severity and impact:

| Severity | Criteria | Action |
|----------|----------|--------|
| P1 | Complete region down, RTO < 15 min | Immediate failover |
| P2 | Partial degradation, RTO < 1 hour | Gradual traffic shift |
| P3 | Non-critical component down | Monitor and fix |

---

## Failover Procedures

### Scenario 1: US-West-2 Region Failure

**Objective**: Redirect all US traffic to EU-West-1

#### Step 1: Verify EU-West-1 Capacity

```bash
# Check EU region health
./scripts/check-regional-health.sh eu-west-1

# Verify node capacity
kubectl config use-context somaagent-eu-west-1
kubectl top nodes

# Check pod capacity
kubectl get pods --all-namespaces | grep -v Running | wc -l
```

#### Step 2: Scale EU-West-1

```bash
# Increase node group size
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name somaagent-eu-west-1-application \
  --desired-capacity 10 \
  --region eu-west-1

# Wait for nodes to be ready
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Scale deployments
kubectl scale deployment orchestrator --replicas=6
kubectl scale deployment gateway-api --replicas=8
kubectl scale deployment slm-service --replicas=10
```

#### Step 3: Update Route53 Weights

```bash
# Reduce US weight to 0, increase EU weight to 100
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://failover-to-eu.json

# Verify change
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --query "ResourceRecordSets[?Name=='api.somaagent.io']"
```

**failover-to-eu.json**:
```json
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.somaagent.io",
        "Type": "A",
        "SetIdentifier": "us-west-2",
        "Weight": 0,
        "AliasTarget": {
          "HostedZoneId": "Z1234567890ABC",
          "DNSName": "somaagent-us-west-2-lb.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.somaagent.io",
        "Type": "A",
        "SetIdentifier": "eu-west-1",
        "Weight": 100,
        "AliasTarget": {
          "HostedZoneId": "Z1234567890DEF",
          "DNSName": "somaagent-eu-west-1-lb.eu-west-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
```

#### Step 4: Monitor Traffic Shift

```bash
# Monitor request rate in EU
kubectl logs -f deployment/gateway-api -n default | grep "region=eu-west-1"

# Check error rates
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/http_requests_errors | jq

# Verify DNS propagation
dig api.somaagent.io +short
```

#### Step 5: Enable Data Replication (if needed)

```bash
# For critical cross-region data only
# Enable replication for session data, user metadata

kubectl apply -f infra/k8s/cross-region-replication.yaml
```

**Expected Timeline**: 10-15 minutes

---

### Scenario 2: EU-West-1 Region Failure

**Objective**: Redirect EU traffic to US-West-2

**NOTE**: Check data residency compliance before redirecting EU user traffic!

#### Step 1: Verify US-West-2 Capacity

```bash
./scripts/check-regional-health.sh us-west-2

kubectl config use-context somaagent-us-west-2
kubectl top nodes
```

#### Step 2: Handle GDPR Compliance

```bash
# EU users MUST stay in EU region
# Option 1: Serve degraded service (read-only mode)
kubectl apply -f infra/k8s/read-only-mode.yaml

# Option 2: Show maintenance page for EU users
# Update Route53 to point to static S3 bucket
```

#### Step 3: Update Route53 (Non-EU traffic only)

```bash
# Shift only non-EU traffic to US
# EU traffic gets maintenance page
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://failover-eu-partial.json
```

**Expected Timeline**: 10-15 minutes (with data residency constraints)

---

## Recovery Procedures

### After Region Restored

#### Step 1: Verify Region Health

```bash
# Check all components
./scripts/check-regional-health.sh us-west-2

# Run smoke tests
./scripts/smoke-test.sh us-west-2
```

#### Step 2: Gradual Traffic Restoration

```bash
# Start with 10% traffic
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://restore-us-10pct.json

# Wait 15 minutes, monitor error rates

# Increase to 50%
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://restore-us-50pct.json

# Wait 15 minutes, monitor

# Restore to normal (50/50)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://restore-normal.json
```

#### Step 3: Verify Data Consistency

```bash
# Check for any data sync issues during failover
kubectl exec -it deployment/orchestrator -- python scripts/verify-data-consistency.py

# Reconcile any discrepancies
kubectl exec -it deployment/orchestrator -- python scripts/reconcile-data.py
```

**Expected Timeline**: 45-60 minutes

---

## Rollback

If failover causes issues:

```bash
# Immediately restore original routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://rollback.json

# Scale down temporary capacity
kubectl scale deployment orchestrator --replicas=3
kubectl scale deployment gateway-api --replicas=4

# Investigate and fix root cause
```

---

## Post-Incident

### Immediate Actions

- [ ] Document incident timeline
- [ ] Capture logs and metrics
- [ ] Notify stakeholders of resolution
- [ ] Update status page

### Follow-Up (Within 48 hours)

- [ ] Schedule post-mortem meeting
- [ ] Identify root cause
- [ ] Create action items for prevention
- [ ] Update runbook with lessons learned
- [ ] Test failover procedure in staging

### Metrics to Review

- **RTO (Recovery Time Objective)**: Target < 15 minutes
- **RPO (Recovery Point Objective)**: Target < 5 minutes of data loss
- **Error Rate**: Should return to baseline within 30 minutes
- **User Impact**: Number of affected users and requests

---

## Quick Reference

### Contact Information

- **On-Call Engineer**: PagerDuty rotation
- **Platform Lead**: @platform-team
- **Security Lead**: @security-team (for GDPR issues)

### Key Commands

```bash
# Check health
./scripts/check-regional-health.sh [region]

# Deploy to region
./scripts/deploy-region.sh [region] apply

# Run DR drill
./scripts/dr-drill.sh

# Verify data residency
./scripts/verify-data-residency.sh [user-id]
```

### Escalation Path

1. **0-15 min**: On-call engineer
2. **15-30 min**: Platform lead
3. **30+ min**: CTO, activate backup team

---

**Remember**: Data residency is CRITICAL. Never route EU user data to non-EU regions without legal approval.
