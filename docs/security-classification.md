# Document Security Classification

![Version](https://img.shields.io/badge/version-1.0.0-blue)

| Classification | Description | Handling Rules |
|----------------|-------------|----------------|
| **Public** | Information that can be shared openly. | No restrictions. |
| **Internal** | Operational details, internal APIs. | Keep in the public repo but mark with `<!-- INTERNAL -->`. |
| **Confidential** | Secrets, vulnerability disclosures, credential handling. | Store only in a **private** repo; reference via `DUMMY_TOKEN_FOR_TESTING` placeholders. |

## SomaAgentHub Classification Examples
- **Public**: Architecture diagrams, API documentation, deployment guides
- **Internal**: Internal service communication patterns, debugging procedures
- **Confidential**: Production credentials, security vulnerability details, private keys