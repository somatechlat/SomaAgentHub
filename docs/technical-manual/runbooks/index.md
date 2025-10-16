# SomaAgentHub Operational Runbooks

**A collection of step-by-step procedures for common operational tasks and alerts.**

This document serves as a central directory for runbooks. Each runbook provides a standardized procedure to diagnose and resolve common issues, ensuring fast and consistent incident response.

---

## 🎯 How to Use These Runbooks

When an alert fires or an operational task is required, follow these steps:

1.  **Identify the Symptom**: Match the alert or issue to the corresponding runbook below.
2.  **Follow the Steps**: Execute the diagnostic and remediation steps exactly as described.
3.  **Document Actions**: Keep a record of the commands run and their output.
4.  **Escalate if Necessary**: If the runbook does not resolve the issue, follow the escalation path.
5.  **Contribute Back**: If you discover a new issue or a better procedure, update the relevant runbook via a pull request.

---

## 📚 Runbook Index

### Critical Alerts
- [**RUNBOOK-001: Service Is Down**](./service-is-down.md)
- [**RUNBOOK-002: High 5xx Error Rate**](./high-5xx-error-rate.md)
- [**RUNBOOK-003: High Request Latency**](./high-request-latency.md)
- [**RUNBOOK-004: Pod Is CrashLooping**](./pod-crashlooping.md)
- [**RUNBOOK-005: Database Is Unavailable**](./database-unavailable.md)

### Routine Operations
- [**RUNBOOK-101: Scaling a Service**](./scaling-a-service.md)
- [**RUNBOOK-102: Performing a Service Rollback**](./performing-a-rollback.md)
- [**RUNBOOK-103: Restarting a Service**](./restarting-a-service.md)
- [**RUNBOOK-104: Database Backup and Restore**](./database-backup-restore.md)

### Security Operations
- [**RUNBOOK-201: Rotating Secrets**](./rotating-secrets.md)
- [**RUNBOOK-202: Investigating a Security Alert**](./investigating-security-alert.md)

---

##  escalation-path.png
![Escalation Path](escalation-path.png)

## 📞 Escalation Path

If a runbook fails to resolve a critical issue within **30 minutes**, escalate immediately.

1.  **Primary On-Call**: The SRE team member currently on-call.
2.  **Secondary On-Call**: The lead SRE or Platform Engineering lead.
3.  **Incident Commander**: For major incidents, an incident commander will be assigned.

Refer to the internal on-call schedule for contact information.

---

## ✍️ Contributing to Runbooks

A runbook is a living document. To contribute:

1.  Create a new markdown file in this directory (e.g., `new-runbook.md`).
2.  Follow the standard runbook template (see below).
3.  Add a link to your new runbook in the index above.
4.  Submit a pull request for review by the SRE team.

### Runbook Template
```markdown
# RUNBOOK-XXX: Clear and Concise Title

| Metadata | Value |
|---|---|
| **Alert Name** | `PrometheusAlertName` |
| **Severity** | P1 (Critical) / P2 (High) / P3 (Medium) |
| **Owner** | SRE Team |
| **Last Updated**| YYYY-MM-DD |

---

### 1. Triage & Diagnosis

**Initial Checks:**
- Check Grafana Dashboard: [Link to relevant dashboard]
- Check recent logs: `kubectl logs ...`

**Diagnostic Steps:**
1.  **Step 1**: `command to run`
    - *Expected Output*: ...
2.  **Step 2**: `another command`
    - *Expected Output*: ...

### 2. Remediation Steps

**Immediate Actions:**
1.  **Action 1**: `command to fix the issue`
2.  **Action 2**: `another command`

**Verification:**
- `command to verify the fix`
- Check Grafana to confirm metrics have returned to normal.

### 3. Escalation

If the issue is not resolved after following these steps, escalate to [Secondary On-Call Contact].

### 4. Post-Mortem / Root Cause Analysis

- Was the alert threshold correct?
- Was the runbook effective?
- What was the root cause of the issue?
- What follow-up actions are needed to prevent recurrence?
```

---
## 🔗 Related Documentation
- **[Monitoring Guide](../monitoring.md)**: For understanding the alerts.
- **[Deployment Guide](../deployment.md)**: For information on service configuration.
```