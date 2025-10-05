# Incident Response Runbook

## Overview
Standard operating procedures for handling production incidents in SomaGent.

## Severity Classification

### P0 - Critical (Page immediately)
- Complete service outage affecting all users
- Data loss or corruption
- Security breach
- Examples: Database down, gateway-api crashed, authentication failure

### P1 - High (Respond within 15 minutes)
- Major feature unavailable
- Significant performance degradation (>5s response times)
- Tool adapter failures affecting >50% of workflows
- Examples: KAMACHIQ down, GitHub adapter rate limited, Redis unavailable

### P2 - Medium (Respond within 1 hour)
- Minor feature degradation
- Single tool adapter failure
- High error rate in specific service
- Examples: Notion sync delayed, capsule marketplace slow

### P3 - Low (Respond within 4 hours)
- Cosmetic issues
- Non-critical monitoring gaps
- Documentation errors

### P4 - Planned (Schedule work)
- Feature requests
- Optimization opportunities
- Technical debt

---

## Incident Response Process

### 1. Detection & Alert
**Who:** On-call engineer receives PagerDuty alert

**Actions:**
1. Acknowledge alert in PagerDuty
2. Check Prometheus dashboard for service health
3. Review recent deployments in #deployments Slack channel
4. Classify severity (P0-P4)

**Prometheus Queries:**
```promql
# Service availability
up{job=~"gateway-api|orchestrator|kamachiq-service"}

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

### 2. Incident Declaration
**Who:** On-call engineer

**Actions:**
1. Create incident in PagerDuty
2. Post in #incidents Slack channel:
   ```
   🚨 INCIDENT DECLARED - P0
   Title: Gateway API Down
   Impact: All API requests failing (100% error rate)
   Assigned: @oncall-engineer
   War room: #incident-<number>
   Status page: https://status.somagent.ai
   ```
3. Create dedicated war room channel: `#incident-1234`
4. Update status page: https://status.somagent.ai

**For P0/P1 only:**
- Page Incident Commander (IC) via PagerDuty
- IC assembles response team (engineers, SRE, product manager)
- Schedule 15-minute sync standups

---

### 3. Investigation & Diagnosis

**Incident Commander Actions:**
1. Delegate investigation tasks
2. Maintain incident timeline in war room
3. Communicate updates every 15 minutes

**Engineering Actions:**

#### Check Service Health
```bash
# All services
kubectl get pods -n somagent-production

# Specific service logs
kubectl logs -n somagent-production deployment/gateway-api --tail=200

# Database connectivity
psql -h $DB_HOST -U somagent -d somagent -c "SELECT 1"

# Redis connectivity
redis-cli -h $REDIS_HOST ping
```

#### Check Recent Changes
```bash
# Recent deployments
kubectl rollout history deployment/gateway-api -n somagent-production

# Recent commits
git log --since="1 hour ago" --oneline
```

#### Check Tool Adapters
```bash
# Tool health endpoint
curl http://localhost:8003/tools/github/health

# Recent tool invocations
curl http://localhost:8003/tools/recent?limit=50
```

#### Check Prometheus Metrics
- Gateway API error rate: `rate(gateway_requests_total{status="500"}[5m])`
- Database connections: `pg_stat_activity_count`
- Redis memory: `redis_memory_used_bytes / redis_memory_max_bytes`

---

### 4. Mitigation

**Common Mitigation Patterns:**

#### Service Crash
```bash
# Rollback to previous version
kubectl rollout undo deployment/gateway-api -n somagent-production

# Scale up replicas
kubectl scale deployment/gateway-api --replicas=5 -n somagent-production

# Force restart
kubectl rollout restart deployment/gateway-api -n somagent-production
```

#### Database Issues
```bash
# Check connection pool
SELECT count(*) FROM pg_stat_activity WHERE datname='somagent';

# Kill long-running queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';

# Restart database (LAST RESORT)
kubectl rollout restart statefulset/postgres -n somagent-production
```

#### Redis Issues
```bash
# Flush cache (if corrupted)
redis-cli FLUSHALL

# Restart Redis
kubectl rollout restart deployment/redis -n somagent-production
```

#### Rate Limit (GitHub, etc.)
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Enable circuit breaker
curl -X POST http://localhost:8003/tools/github/circuit-breaker/enable

# Wait for rate limit reset (usually 1 hour)
```

#### High Load
```bash
# Scale horizontally
kubectl scale deployment/gateway-api --replicas=10 -n somagent-production

# Enable autoscaling
kubectl autoscale deployment/gateway-api --min=3 --max=10 --cpu-percent=70
```

---

### 5. Communication

**Update Frequency:**
- P0: Every 15 minutes
- P1: Every 30 minutes
- P2: Every 1 hour

**Channels:**
- War room (#incident-<number>)
- #general (customer-facing updates)
- Status page (https://status.somagent.ai)

**Template:**
```
Update #3 - 14:45 UTC
Status: Investigating
Impact: Gateway API 503 errors affecting 80% of requests
Actions: Rolled back deployment to v1.2.3, monitoring recovery
Next update: 15:00 UTC
```

---

### 6. Resolution

**Actions:**
1. Verify metrics returned to normal
2. Test critical user flows
3. Post resolution in war room:
   ```
   ✅ RESOLVED - 15:30 UTC
   Root cause: Database connection pool exhaustion
   Fix: Increased max_connections from 100 to 200
   Duration: 45 minutes
   ```
4. Update status page to "Resolved"
5. Close PagerDuty incident

---

### 7. Post-Incident Review (PIR)

**Within 48 hours of resolution**

**Participants:**
- Incident Commander
- Response team
- Engineering leadership
- Product manager

**PIR Document Template:**

```markdown
# Post-Incident Review: Gateway API Outage (2024-01-15)

## Summary
- **Date:** 2024-01-15 14:00 UTC
- **Duration:** 45 minutes
- **Severity:** P0
- **Impact:** 100% of API requests failed

## Timeline
- 14:00 - Alert triggered (gateway_api_down)
- 14:03 - Incident declared, IC paged
- 14:05 - Investigation started
- 14:15 - Root cause identified (DB connection pool exhaustion)
- 14:20 - Mitigation applied (increased max_connections)
- 14:30 - Service recovered
- 14:45 - Incident resolved

## Root Cause
Database connection pool exhausted due to spike in traffic from new customer onboarding.

## What Went Well
- Alert fired within 30 seconds
- IC responded in 3 minutes
- Clear war room communication

## What Went Wrong
- No autoscaling configured
- Database connection limits too low
- Missing capacity planning for traffic spike

## Action Items
- [ ] Configure autoscaling for gateway-api (@alice, Due: 2024-01-20)
- [ ] Increase DB connection pool to 500 (@bob, Due: 2024-01-18)
- [ ] Add capacity planning dashboard (@charlie, Due: 2024-01-25)
- [ ] Document connection pool tuning (@david, Due: 2024-01-22)

## Lessons Learned
1. Always load test before major customer onboarding
2. Autoscaling should be default for all services
3. Database connection pool should scale with replica count
```

---

## Escalation Paths

### On-Call Rotation
- **Primary:** Current on-call engineer (PagerDuty)
- **Secondary:** Backup on-call (PagerDuty)
- **Escalation:** Engineering Manager (after 15 min)
- **Final:** VP Engineering / CTO

### Incident Commander
- **P0/P1:** Senior Engineer or Engineering Manager
- **P2/P3:** On-call engineer can self-IC

### External Escalation
- **Customer Success:** For customer impact communication
- **Legal:** For security incidents or data breaches
- **PR/Marketing:** For public incidents affecting brand

---

## Emergency Contacts

| Role | Primary | Secondary |
|------|---------|-----------|
| On-Call Engineer | PagerDuty rotation | PagerDuty rotation |
| Incident Commander | Engineering Manager | Senior Engineer |
| Database Admin | Alice (@alice) | Bob (@bob) |
| Security Lead | Charlie (@charlie) | David (@david) |
| VP Engineering | Eve (@eve) | Frank (@frank) |

---

## Common Incident Scenarios

### Gateway API Down
1. Check Kubernetes pod status
2. Review recent deployments
3. Check database connectivity
4. Rollback if recent deployment
5. Scale up replicas

### Database Performance Issues
1. Check slow query log
2. Terminate long-running queries
3. Increase connection pool
4. Enable read replicas

### Tool Adapter Failures
1. Check rate limits
2. Verify API credentials
3. Enable circuit breaker
4. Fallback to alternative tools

### Memory Leak
1. Identify service with high memory
2. Capture heap dump
3. Restart affected pods
4. File bug with heap dump

### Security Incident
1. **IMMEDIATELY** page Security Lead
2. Isolate affected systems
3. Preserve logs for forensics
4. Follow security runbook (see docs/runbooks/security.md)
5. Notify legal if data breach suspected

---

## Tools & Dashboards

- **Prometheus:** http://prometheus.somagent.ai
- **Grafana:** http://grafana.somagent.ai
- **PagerDuty:** https://somagent.pagerduty.com
- **Status Page:** https://status.somagent.ai
- **Kubernetes Dashboard:** https://k8s.somagent.ai
- **Logs:** `kubectl logs` or https://logs.somagent.ai

---

## References
- [Tool Health Monitoring](./tool_health_monitoring.md)
- [Scaling Procedures](./scaling_procedures.md)
- [Disaster Recovery](./disaster_recovery_extended.md)
- [Security Runbook](./security.md)
