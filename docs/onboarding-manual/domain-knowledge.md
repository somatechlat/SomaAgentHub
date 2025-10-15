# SomaAgentHub Domain Knowledge

**An introduction to the core concepts and terminology of the SomaAgentHub platform.**

This document provides a deeper dive into the key concepts that underpin SomaAgentHub. Understanding these ideas is essential for contributing effectively to the codebase.

---

## 🎯 Core Concepts

### 1. Multi-Agent Orchestration
This is the central idea of SomaAgentHub. Instead of a single AI model trying to do everything, we coordinate a team of specialized **agents**.

- **Agent**: An AI-powered entity designed for a specific task (e.g., a `ResearchAgent`, a `CodeWritingAgent`).
- **Orchestration**: The process of managing the workflow, communication, and state between these agents to achieve a complex goal.
- **Why it matters**: It allows us to solve problems that are too large or complex for a single agent, leading to more robust and capable AI systems.

### 2. Workflows
A workflow is a structured, multi-step process that is executed by the **Orchestrator Service**.

- **Powered by Temporal**: We use a technology called Temporal to make our workflows durable and resilient. A workflow can run for seconds, hours, or even days, and it will survive server restarts.
- **Activities**: The individual steps within a workflow are called "activities." An activity might be "call the OpenAI API" or "query the database."

### 3. Intelligent Memory
Agents need a way to remember things. The **Memory Gateway** provides this capability.

- **Semantic Search**: It uses a vector database (Qdrant) to allow agents to search for information based on meaning, not just keywords. This is also known as Retrieval-Augmented Generation (RAG).
- **Conversation History**: It stores past conversations so that agents can maintain context over long interactions.

### 4. Policy Engine & Constitutional AI
To ensure our agents behave safely and ethically, we use a **Policy Engine**.

- **Constitutional AI**: This is the principle of giving an AI a set of rules or a "constitution" to follow.
- **How it works**: Before an agent performs a significant action, the Orchestrator checks with the Policy Engine to ensure the action complies with the defined rules.

---

## 📚 Glossary of Key Terms

| Term | Definition |
|---|---|
| **Agent** | An autonomous AI entity specialized for a task. |
| **Orchestrator** | The core service that manages multi-agent workflows. |
| **Workflow** | A durable, multi-step process managed by the Orchestrator. |
| **Temporal** | The underlying technology that powers our workflows. |
| **Activity** | A single step within a Temporal workflow. |
| **Memory Gateway**| The service that provides long-term memory for agents. |
| **Qdrant** | The vector database we use for semantic search. |
| **RAG** | Retrieval-Augmented Generation; the process of retrieving relevant information to augment a prompt to an LLM. |
| **Policy Engine**| The service that enforces safety and governance rules. |
| **Gateway API** | The main public-facing entry point to the platform. |

---
## 🔗 Next Steps
With this context, you are now well-equipped to explore the codebase with a deeper understanding.
- **[Codebase Walkthrough](./codebase-walkthrough.md)**: Re-read this document to see how these concepts map to the actual service directories.
```