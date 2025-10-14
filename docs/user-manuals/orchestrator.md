# Orchestrator – User Manual

## Overview
The Orchestrator is the central component of the SomaAgentHub platform, responsible for managing complex workflows and coordinating the execution of tasks. It leverages Temporal for durable, long-running workflows and can delegate tasks to a variety of specialized agent frameworks.

## Features
- **Workflow Management:** The Orchestrator uses Temporal to manage complex, long-running workflows. This includes the `KAMACHIQProjectWorkflow` for autonomous project execution and the `AgentTaskWorkflow` for individual agent tasks.
- **Task Decomposition:** The Orchestrator can decompose high-level tasks into smaller, manageable sub-tasks.
- **Task Planning:** It can create detailed execution plans for the decomposed tasks.
- **Agent Integration:** The Orchestrator can delegate tasks to a variety of agent frameworks, including:
    - **a2a:** For agent-to-agent communication.
    - **AutoGen:** For multi-agent conversations.
    - **CrewAI:** For collaborative agent-based workflows.
    - **LangGraph:** For building stateful, multi-agent applications.

## Endpoints

### System
- `GET /health`: Performs a health check of the service.
- `GET /ready`: Indicates if the service is ready to accept traffic.
- `GET /metrics`: Exposes Prometheus metrics.

### API
- The Orchestrator's API is primarily used by the Gateway API and other internal services. It includes endpoints for managing conversations, projects, and training.

## Usage
The Orchestrator is not typically accessed directly by end-users. It is driven by requests from the Gateway API and by Temporal workers.

## Notes
- Policies are enforced by the Policy Engine before any tasks are executed.
