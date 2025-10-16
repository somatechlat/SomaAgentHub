# SomaAgentHub Secrets Management Policy

**Official policy for the secure handling of secrets within the SomaAgentHub platform.**

This document defines the policies and procedures for managing all sensitive information (secrets), including passwords, API keys, and certificates. Adherence to this policy is mandatory for all personnel.

---

## 1. Policy Statement

All secrets required for the operation of the SomaAgentHub platform must be managed in a secure, centralized, and auditable manner. Plain-text secrets are strictly forbidden in Git repositories, configuration files, and container images.

## 2. Scope

This policy applies to:
- Database credentials
- API keys for third-party services (e.g., OpenAI)
- JWT signing keys
- TLS certificates and private keys
- Any other sensitive credentials

## 3. Secrets Storage

**Production Environments:**
- **Primary Method**: A dedicated secrets management tool such as **HashiCorp Vault**, **AWS Secrets Manager**, or **Google Secret Manager** is required.
- **Alternative**: Kubernetes Secrets can be used, but they must be managed with a tool that provides encryption at rest, such as **Sealed Secrets**.

**Development Environments:**
- Kubernetes Secrets may be used directly for local development, but these secrets must not be production secrets.

## 4. Secret Creation and Naming

- **Generation**: Secrets must be generated with sufficient entropy (e.g., `openssl rand -base64 32`).
- **Naming Convention**: Secrets in Kubernetes should follow the pattern `<app-name>-<secret-type>-<environment>`, e.g., `soma-platform-db-credentials-prod`.

## 5. Access Control

- **Principle of Least Privilege**: Access to secrets must be granted on a need-to-know basis.
- **RBAC**: Use the RBAC capabilities of your secrets management tool or Kubernetes to restrict access.
- **Audit Logging**: All access to secrets (read, write, delete) must be logged and audited regularly.

## 6. Secret Rotation

- **Rotation Schedule**: All secrets must be rotated at least every **90 days**. Critical secrets, such as the JWT signing key, should be rotated more frequently if a compromise is suspected.
- **Automated Rotation**: Where possible, rotation should be automated.

## 7. Prohibited Practices

- **❌ Storing secrets in Git.**
- **❌ Hardcoding secrets in application code.**
- **❌ Passing secrets as environment variables in plain text.** (Use Kubernetes secretKeyRef).
- **❌ Sharing secrets over insecure channels** (e.g., Slack, email).

---
## 🔗 Related Documentation
- **[Security Guide](./index.md)**: For the overall security architecture.
