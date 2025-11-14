# Glossary

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Core Terms

**Agent**: Autonomous software entity that performs tasks using tools, memory, and policy constraints.

**Capsule**: Reusable execution bundle containing tools, prompts, and policies for specific tasks.

**Gateway API**: Public-facing FastAPI service (port 10000) that handles wizard flows and external requests.

**Helm Chart**: Kubernetes package manager template for deploying SomaAgentHub services.

**Kind**: Kubernetes in Docker - local development cluster tool.

**MAO Service**: Multi-Agent Orchestrator service that coordinates complex workflows.

**Memory Gateway**: Service (port 10021) providing vector and key-value storage via Qdrant integration.

**Orchestrator**: Central coordination service (port 10001) managing Temporal workflows and agent sessions.

**Policy Engine**: Rule-based guardrail service (port 10020) enforcing compliance and governance.

**Session**: Stateful conversation context maintained across agent interactions.

**Temporal**: Workflow orchestration platform providing durable execution and retry logic.

**Wizard Flow**: Multi-step guided process for launching agent workflows through the Gateway API.

## Technical Terms

**FastAPI**: Python web framework used for all HTTP services in SomaAgentHub.

**Qdrant**: Vector database used for semantic search and agent memory storage.

**Redis**: In-memory data store used for session state and real-time context sharing.

**SPIFFE/SPIRE**: Zero-trust identity framework for service-to-service authentication.

**Volcano**: Kubernetes batch scheduler for high-performance computing workloads.

## Infrastructure Terms

**Namespace**: Kubernetes logical cluster subdivision (default: soma-agent-hub).

**ServiceMonitor**: Prometheus configuration for automated metrics scraping.

**PodGroup**: Volcano scheduler resource for gang scheduling multiple pods.

**Ingress**: Kubernetes resource managing external access to services.