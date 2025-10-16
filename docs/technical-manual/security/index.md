# SomaAgentHub Security Guide

**A guide to security configuration, best practices, and compliance for SomaAgentHub.**

This document provides a comprehensive overview of the security architecture, procedures, and best practices for securing a SomaAgentHub deployment. It is intended for Security Engineers, SREs, and System Administrators.

---

## 🎯 Security Architecture

SomaAgentHub is designed with a defense-in-depth strategy, incorporating security at every layer of the platform.

| Layer | Security Control | Implementation |
|---|---|---|
| **Network** | TLS Encryption, Network Policies | All public traffic is over HTTPS. Kubernetes NetworkPolicies restrict pod-to-pod communication. |
| **Authentication**| JWT Tokens | All API requests are authenticated using short-lived JSON Web Tokens issued by the Identity Service. |
| **Authorization** | Role-Based Access Control (RBAC)| The Identity Service manages roles and permissions, ensuring users and agents can only access authorized resources. |
| **Secrets** | Secrets Management | All sensitive data (API keys, passwords) is stored in Kubernetes Secrets and mounted into pods at runtime. |
| **Container** | Image Scanning, Minimal Base Images| Docker images are scanned for vulnerabilities using Trivy. Base images are hardened and minimal. |
| **Application** | Input Validation, Policy Engine | FastAPI provides input validation. The Policy Engine enforces constitutional rules on agent behavior. |
| **Audit** | Audit Logging | All significant actions (API calls, logins, workflow changes) are logged for security auditing. |

---

## 🔐 Secrets Management

Proper management of secrets is critical to the security of the platform.

### [Secrets Policy](./secrets-policy.md)
This document outlines the official policy for creating, storing, rotating, and accessing secrets within the SomaAgentHub environment. **All engineers must read and adhere to this policy.**

### Rotation Procedure
Secrets such as database passwords and JWT signing keys should be rotated regularly.

**Recommended Rotation Schedule:** Every 90 days.

**Procedure:**
1.  **Generate a new secret value.**
2.  **Update the Kubernetes Secret:**
    ```bash
    kubectl edit secret soma-platform-secrets -n soma-agent-hub
    # Update the relevant base64-encoded value.
    ```
3.  **Perform a rolling restart** of all services that use the secret to ensure they pick up the new value.
    ```bash
    kubectl rollout restart deployment -n soma-agent-hub
    ```

For production environments, we strongly recommend using a dedicated secrets management tool like **HashiCorp Vault** or **AWS Secrets Manager** for automated rotation and centralized control.

---

## 👤 Access Control (RBAC)

Access to the platform is governed by a Role-Based Access Control (RBAC) model.

### [RBAC Matrix](./rbac-matrix.md)
This document provides a detailed matrix of all available roles (e.g., `Admin`, `Developer`, `Viewer`) and the specific permissions granted to each.

### How it Works
1.  The **Identity Service** is the source of truth for user roles.
2.  When a user logs in, they are issued a JWT token containing their role claims.
3.  The **Gateway API** and other services inspect this token on every request to authorize the action.

---

## 🛡️ Hardening Guide

Follow these best practices to harden your production deployment.

### 1. Network Security
- **Restrict Ingress**: Configure your Ingress controller and firewall to only allow traffic on required ports (typically 443).
- **Apply Network Policies**: Use Kubernetes NetworkPolicies to enforce a "zero-trust" network model, only allowing services to communicate with their explicit dependencies.

### 2. Kubernetes Security
- **Use a dedicated namespace**: As deployed by the Helm chart (`soma-agent-hub`).
- **Run as non-root**: All container images are configured to run with a non-root user.
- **Read-only root filesystem**: Where possible, containers should run with a read-only root filesystem.
- **Pod Security Admission**: Enforce `baseline` or `restricted` pod security standards on the namespace.

### 3. Application Security
- **Keep dependencies updated**: Regularly scan for and patch vulnerabilities in application dependencies.
- **Configure the Policy Engine**: Define and enforce strict constitutional policies to govern agent behavior and prevent misuse.

---

## 📜 Compliance

SomaAgentHub includes features to help organizations meet their compliance obligations (e.g., GDPR, CCPA).

- **Audit Logs**: Provide a complete, immutable record of all system activity.
- **Data Management**: Features for data export and deletion to comply with "right to be forgotten" requests.
- **Data Residency**: Deploy the platform to a specific geographic region to meet data residency requirements.

---

## 🔗 Related Documentation
- **[Secrets Policy](./secrets-policy.md)**: Detailed policy on secrets management.
- **[RBAC Matrix](./rbac-matrix.md)**: Detailed breakdown of roles and permissions.
- **[Deployment Guide](../deployment.md)**: For security-related deployment configurations.
```