# RUNBOOK-001: Service Is Down

| Metadata | Value |
|---|---|
| **Alert Name** | `ServiceDown` |
| **Severity** | P1 (Critical) |
| **Owner** | SRE Team |
| **Last Updated**| 2024-10-15 |

---

This runbook is triggered when the `up` metric from Prometheus is `0` for a core service for more than 5 minutes.

### 1. Triage & Diagnosis

**Initial Checks:**
- **Grafana Dashboard**: [Platform Overview Dashboard](http://localhost:10011/d/platform-overview)
- **Alerting Service**: Check which service is reported as down in the alert notification.

**Diagnostic Steps:**

1.  **Check Pod Status:**
    Identify the pods for the failing service (e.g., `gateway-api`).
    ```bash
    export SERVICE_NAME="gateway-api" # Replace with the failing service name
    kubectl get pods -n soma-agent-hub -l app=$SERVICE_NAME
    ```
    - *Expected Output*: All pods for the service should be in the `Running` state.
    - *Common Issues*: Pods are `CrashLoopBackOff`, `Pending`, or `ImagePullBackOff`.

2.  **Check Pod Logs:**
    Review the logs of a failing pod to find the root cause.
    ```bash
    export POD_NAME=$(kubectl get pods -n soma-agent-hub -l app=$SERVICE_NAME -o jsonpath='{.items[0].metadata.name}')
    kubectl logs -n soma-agent-hub $POD_NAME
    ```
    - *Look For*: Error messages, stack traces, database connection errors, or configuration issues.

3.  **Check Pod Events:**
    Events can reveal issues with scheduling or resource allocation.
    ```bash
    kubectl describe pod -n soma-agent-hub $POD_NAME
    ```
    - *Look For*: `FailedScheduling` (resource issues), `FailedMount` (storage issues), `Unhealthy` (failed probes).

4.  **Check Dependencies:**
    A service may be down because a critical dependency (like a database) is unavailable.
    ```bash
    # Check PostgreSQL health
    kubectl exec -n soma-agent-hub <postgres-pod> -- pg_isready
    # Check Redis health
    kubectl exec -n soma-agent-hub <redis-pod> -- redis-cli ping
    ```

### 2. Remediation Steps

**Immediate Actions:**

1.  **Restart the Service:**
    A simple restart often resolves transient issues.
    ```bash
    kubectl rollout restart deployment/$SERVICE_NAME -n soma-agent-hub
    ```
    Monitor the new pods to ensure they start correctly.

2.  **Scale Up Dependencies (if resource-related):**
    If logs or events indicate resource exhaustion, scale up the affected dependency.
    ```bash
    # Example: Scale up PostgreSQL resources
    helm upgrade ... --set postgresql.resources.requests.memory=4Gi
    ```

3.  **Roll Back to a Previous Version:**
    If the issue started after a recent deployment, roll back to the last known good version.
    ```bash
    helm rollback soma-agent-hub <previous-revision-number> -n soma-agent-hub
    ```

### 3. Escalation

If the service does not recover within **15 minutes** after following these steps, escalate to the **Secondary On-Call Engineer**. Provide them with the output of the diagnostic commands you have run.

### 4. Post-Mortem / Root Cause Analysis
- Was this a transient issue or a recurring problem?
- If it was a bug, has a ticket been created?
- Do the liveness/readiness probes need to be adjusted?
- Was the failure caused by a resource limit that needs to be increased?
```