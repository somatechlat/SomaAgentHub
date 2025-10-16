# SomaAgentHub RBAC Matrix

**Role-Based Access Control matrix defining user roles and permissions.**

This document provides a detailed breakdown of the roles and permissions used to control access to the SomaAgentHub platform.

---

## 🎯 Roles Overview

| Role | Audience | Purpose |
|---|---|---|
| **Viewer** | Business Analysts, Stakeholders | Read-only access to view workflows and results. |
| **Operator** | End-Users, Operations Teams | Can run and manage workflows. |
| **Developer** | Software Engineers | Can create and modify workflow definitions and tools. |
| **Admin** | System Administrators, SREs | Full control over the system, including user and security settings. |

---

## Permissions Matrix

| Action | Viewer | Operator | Developer | Admin |
|---|:---:|:---:|:---:|:---:|
| **Workflows** | | | | |
| View Workflows | ✅ | ✅ | ✅ | ✅ |
| Run Workflow | ❌ | ✅ | ✅ | ✅ |
| Cancel Workflow | ❌ | ✅ | ✅ | ✅ |
| Create/Edit Workflow | ❌ | ❌ | ✅ | ✅ |
| Delete Workflow | ❌ | ❌ | ❌ | ✅ |
| **Memory** | | | | |
| View Memory | ✅ | ✅ | ✅ | ✅ |
| Add to Memory | ❌ | ✅ | ✅ | ✅ |
| Delete Memory | ❌ | ❌ | ❌ | ✅ |
| **Tools** | | | | |
| View Tools | ✅ | ✅ | ✅ | ✅ |
| Use Tools | ❌ | ✅ | ✅ | ✅ |
| Register/Edit Tool | ❌ | ❌ | ✅ | ✅ |
| **Users & Security** | | | | |
| View Users | ❌ | ❌ | ❌ | ✅ |
| Invite/Manage Users | ❌ | ❌ | ❌ | ✅ |
| View Roles | ❌ | ❌ | ❌ | ✅ |
| Manage Roles | ❌ | ❌ | ❌ | ✅ |
| **System Settings** | | | | |
| View Settings | ✅ | ✅ | ✅ | ✅ |
| Edit Settings | ❌ | ❌ | ❌ | ✅ |

---
## 🔗 Related Documentation
- **[Security Guide](./index.md)**: For the overall security architecture.
