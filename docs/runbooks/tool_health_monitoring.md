# Tool Health Monitoring Runbook

## Overview
Procedures for monitoring, diagnosing, and maintaining health of all tool adapters in SomaAgentHub.

## Tool Adapter Inventory

| Tool | Adapter | Port | Health Endpoint | Rate Limits |
|------|---------|------|----------------|-------------|
| GitHub | `github_adapter.py` | 8003 | `/tools/github/health` | 5000/hour |
| Slack | `slack_adapter.py` | 8003 | `/tools/slack/health` | 1/second |
| Notion | `notion_adapter.py` | 8003 | `/tools/notion/health` | 3/second |
| Plane | `plane_adapter.py` | 8003 | `/tools/plane/health` | Unlimited |
| Jira | `jira_adapter.py` | 8003 | `/tools/jira/health` | 600/min |
| AWS | `aws_adapter.py` | 8003 | `/tools/aws/health` | Varies by service |
| Terraform | `terraform_adapter.py` | 8003 | `/tools/terraform/health` | N/A (local) |
| Kubernetes | `kubernetes_adapter.py` | 8003 | `/tools/kubernetes/health` | N/A (in-cluster) |
| Playwright | `playwright_adapter.py` | 8003 | `/tools/playwright/health` | N/A (local) |
| Linear | `linear_adapter.py` | 8003 | `/tools/linear/health` | 2000/hour |
| GitLab | `gitlab_adapter.py` | 8003 | `/tools/gitlab/health` | 600/min |
| Discord | `discord_adapter.py` | 8003 | `/tools/discord/health` | 50/second |
| Azure | `azure_adapter.py` | 8003 | `/tools/azure/health` | Varies |
| GCP | `gcp_adapter.py` | 8003 | `/tools/gcp/health` | Varies |
| Confluence | `confluence_adapter.py` | 8003 | `/tools/confluence/health` | 300/min |
| Figma | `figma_adapter.py` | 8003 | `/tools/figma/health` | 1000/hour |

---

## Health Check Procedures

### Manual Health Check
```bash
# Check all tools
curl http://localhost:8003/health

# Check specific tool
curl http://localhost:8003/tools/github/health

# Expected response
{
  "status": "healthy",
  "adapter": "github",
  "rate_limit_remaining": 4850,
  "rate_limit_reset": "2024-01-15T15:00:00Z",
  "last_request_latency_ms": 145
}
```

### Automated Monitoring (Prometheus)
```promql
# Tool adapter availability
up{job="tool-service"}

# Tool invocation success rate
sum(rate(tool_invocation_success_total[5m])) by (tool_name) /
sum(rate(tool_invocation_total[5m])) by (tool_name)

# Tool invocation P95 latency
histogram_quantile(0.95, 
  rate(tool_invocation_duration_seconds_bucket[5m])
) by (tool_name)

# Rate limit status
tool_rate_limit_remaining / tool_rate_limit_total
```

---

## Alert Response Procedures

### Alert: ToolInvocationLatencyHigh
**Trigger:** P95 latency > 200ms for 5 minutes

**Diagnosis:**
1. Check which tool is slow:
   ```bash
   curl http://localhost:8003/metrics | grep tool_invocation_duration
   ```

2. Check external API status:
   - GitHub: https://www.githubstatus.com
   - Slack: https://status.slack.com
   - Notion: https://status.notion.so
   - Jira: https://status.atlassian.com

3. Test direct API call:
   ```bash
   # GitHub example
   time curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

**Mitigation:**
- If external API slow: Enable caching, increase timeout
- If network issue: Check AWS network connectivity
- If local CPU: Scale up tool-service replicas

```bash
kubectl scale deployment/tool-service --replicas=5 -n somagent-production
```

---

### Alert: ToolInvocationFailureRateHigh
**Trigger:** Failure rate > 5% for 3 minutes

**Diagnosis:**
1. Check error logs:
   ```bash
   kubectl logs -n somagent-production deployment/tool-service --tail=500 | grep ERROR
   ```

2. Common errors:
   - `401 Unauthorized`: Invalid credentials
   - `429 Too Many Requests`: Rate limited
   - `503 Service Unavailable`: External API down
   - `TimeoutError`: Network or performance issue

**Mitigation by Error:**

#### 401 Unauthorized
```bash
# Verify credentials in Vault
vault kv get secret/tools/github

# Rotate credentials
vault kv put secret/tools/github token=ghp_newtoken...

# Restart tool-service to reload
kubectl rollout restart deployment/tool-service -n somagent-production
```

#### 429 Rate Limited
```bash
# Enable circuit breaker
curl -X POST http://localhost:8003/tools/github/circuit-breaker/enable

# Check rate limit status
curl http://localhost:8003/tools/github/rate-limit

# Wait for reset or request limit increase from provider
```

#### 503 External API Down
```bash
# Check provider status page
# Enable fallback mode (if available)
curl -X POST http://localhost:8003/tools/github/fallback/enable

# Use alternative tool (e.g., GitLab instead of GitHub)
```

---

### Alert: GitHubRateLimitApproaching
**Trigger:** < 10% of rate limit remaining for 5 minutes

**Actions:**
1. Check current usage:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

2. Enable request throttling:
   ```bash
   # Reduce request rate to 80% of limit
   curl -X POST http://localhost:8003/tools/github/throttle \
     -d '{"max_requests_per_hour": 4000}'
   ```

3. Implement caching:
   ```bash
   # Enable Redis caching for GET requests
   curl -X POST http://localhost:8003/tools/github/cache/enable
   ```

4. Request higher rate limit:
   - Contact GitHub support
   - Upgrade to GitHub Enterprise if needed

---

### Alert: ToolAdapterDown
**Trigger:** Tool health check failing for 1 minute

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n somagent-production -l app=tool-service

# Check logs
kubectl logs -n somagent-production deployment/tool-service --tail=100

# Check service connectivity
kubectl exec -n somagent-production deployment/gateway-api -- \
  curl http://tool-service:8003/health
```

**Mitigation:**
```bash
# Restart tool-service
kubectl rollout restart deployment/tool-service -n somagent-production

# If persistent, check for:
# - Missing environment variables
# - Vault connectivity issues
# - Network policies blocking external APIs
```

---

## Rate Limit Management

### Monitoring Rate Limits
```bash
# GitHub
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Slack (via tool-service)
curl http://localhost:8003/tools/slack/rate-limit

# Jira (via tool-service)
curl http://localhost:8003/tools/jira/rate-limit
```

### Rate Limit Strategies

#### 1. Request Throttling
```python
# In adapter code
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=4500, period=3600)  # 4500 per hour (90% of GitHub limit)
def _request(self, method, endpoint, **kwargs):
    # ... request logic
```

#### 2. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_repository(self, repo_name):
    # Cache GET requests
    return self._request("GET", f"/repos/{repo_name}")
```

#### 3. Batching
```python
# GraphQL for batching (GitHub)
query = """
{
  repo1: repository(owner: "org", name: "repo1") { name }
  repo2: repository(owner: "org", name: "repo2") { name }
  repo3: repository(owner: "org", name: "repo3") { name }
}
"""
```

#### 4. Circuit Breaker
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def _request(self, method, endpoint, **kwargs):
    # Automatically stop requests after 5 failures
    # Resume after 60 seconds
```

---

## Circuit Breaker Operations

### Check Circuit Breaker Status
```bash
curl http://localhost:8003/tools/github/circuit-breaker/status

# Response
{
  "state": "closed",  # closed, open, half_open
  "failure_count": 2,
  "last_failure": "2024-01-15T14:30:00Z"
}
```

### Manual Circuit Breaker Control
```bash
# Open circuit (stop all requests)
curl -X POST http://localhost:8003/tools/github/circuit-breaker/open

# Close circuit (resume requests)
curl -X POST http://localhost:8003/tools/github/circuit-breaker/close

# Reset failure count
curl -X POST http://localhost:8003/tools/github/circuit-breaker/reset
```

---

## Credential Rotation

### GitHub Token Rotation
```bash
# 1. Generate new token at https://github.com/settings/tokens
# 2. Update Vault
vault kv put secret/tools/github token=ghp_newtokenhere

# 3. Restart tool-service
kubectl rollout restart deployment/tool-service -n somagent-production

# 4. Verify
curl http://localhost:8003/tools/github/health
```

### Slack Token Rotation
```bash
vault kv put secret/tools/slack \
  bot_token=xoxb-new... \
  user_token=xoxp-new...

kubectl rollout restart deployment/tool-service -n somagent-production
```

### AWS Credentials Rotation
```bash
# Use AWS Secrets Manager auto-rotation
aws secretsmanager rotate-secret --secret-id somagent/aws/credentials

# Or manually update Vault
vault kv put secret/tools/aws \
  access_key_id=AKIAIOSFODNN7EXAMPLE \
  secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Performance Tuning

### Increase Timeout
```bash
# For slow external APIs (default: 30s)
export TOOL_REQUEST_TIMEOUT=60

kubectl set env deployment/tool-service TOOL_REQUEST_TIMEOUT=60 -n somagent-production
```

### Enable Connection Pooling
```python
# In adapter code
import requests

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=100,
    pool_maxsize=100
)
session.mount('https://', adapter)
```

### Horizontal Scaling
```bash
# Scale tool-service for high load
kubectl scale deployment/tool-service --replicas=10 -n somagent-production

# Enable autoscaling
kubectl autoscale deployment/tool-service \
  --min=3 --max=15 --cpu-percent=70 -n somagent-production
```

---

## Debugging Tool Failures

### Enable Debug Logging
```bash
# Set log level to DEBUG
kubectl set env deployment/tool-service LOG_LEVEL=DEBUG -n somagent-production

# Watch logs
kubectl logs -f deployment/tool-service -n somagent-production
```

### Test Tool Directly
```python
# Python REPL test
from services.tool_service.adapters.github_adapter import GitHubAdapter

adapter = GitHubAdapter(token="ghp_...")
result = adapter.get_authenticated_user()
print(result)
```

### Network Debugging
```bash
# DNS resolution
kubectl exec -n somagent-production deployment/tool-service -- \
  nslookup api.github.com

# Connectivity test
kubectl exec -n somagent-production deployment/tool-service -- \
  curl -v https://api.github.com

# Check network policies
kubectl get networkpolicies -n somagent-production
```

---

## Fallback Strategies

### Alternative Tools
- GitHub down → GitLab
- Slack down → Discord
- Jira down → Linear
- AWS down → Azure/GCP
- Notion down → Confluence

### Graceful Degradation
```python
try:
    result = github_adapter.create_repository(name)
except RateLimitError:
    # Fallback to queuing
    queue_repository_creation(name)
    return {"status": "queued", "eta": "1 hour"}
except Exception:
    # Fallback to manual process
    send_notification("Manual GitHub repo creation needed")
    return {"status": "manual", "ticket": "TOOL-123"}
```

---

## References
- [Incident Response](./incident_response.md)
- [Scaling Procedures](./scaling_procedures.md)
- [Prometheus Alerting Rules](../../infra/monitoring/alerting-rules.yml)
- [Tool Adapter Code](../../services/tool-service/adapters/)
