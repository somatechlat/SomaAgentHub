# SomaAgentHub Platform Architecture

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. All architecture and flows reflect real, running systems.

Last Updated: October 9, 2025

> This document provides a high-level view of the platform architecture, components, and data flows.

```mermaid
flowchart LR
  subgraph Client
    U[User]
  end

  subgraph Edge
    GW[Gateway API]
  end

  subgraph Core[Core Services]
    ORCH[Orchestrator]
    POLICY[Policy Engine]
    IDP[Identity Service]
    TOOL[Tool Service]
  end

  subgraph Intelligence
    SLM[SLM Service]
    MEM[Memory Gateway]
  end

  subgraph Infra[Infrastructure]
    KAFKA[(Kafka)]
    PROM[(Prometheus)]
    LOKI[(Loki)]
    TEMPORAL[(Temporal)]
  end

  U -->|HTTP| GW
  GW -->|HTTP| ORCH
  ORCH -->|HTTP| POLICY
  ORCH -->|HTTP| IDP
  ORCH -->|HTTP| SLM
  ORCH -->|HTTP| TOOL
  TOOL -->|HTTP| EXT[External APIs]
  ORCH -->|Events| KAFKA
  GW -->|Events| KAFKA
  SLM -->|Metrics| PROM
  ORCH -->|Metrics| PROM
  GW -->|Metrics| PROM
  GW -->|Logs| LOKI
  ORCH -->|Logs| LOKI
  SLM -->|Logs| LOKI
  ORCH -->|Workflows| TEMPORAL
```

## Component Responsibilities

- Gateway API: Edge entrypoint, auth enforcement, routing
- Orchestrator: Workflow coordination, policy checks, and task execution
- Policy Engine: Authorization decisions and policy evaluation
- Identity Service: Token issuing and user identity verification
- SLM Service: Deterministic local language capabilities
- Memory Gateway: Vector storage / RAG
- Kafka: Event streaming backbone (KRaft mode)
- Prometheus/Loki: Observability stack
- Temporal: Durable workflow orchestration

## Deployment Topology (Helm + K8s)

- Each service is templated via Helm with standard labels.
- Gateway is NodePort (default 30080 → 8080) for local, can be ClusterIP/Ingr ess in production.
- slm-service is ClusterIP on port 1001.
- Observability stack deployed in observability namespace (optional).

## Diagrams

### System Overview
```mermaid
%%{init: { 'theme': 'default' }}%%
%% See docs/diagrams/System_Overview.mmd for source
flowchart LR
  U[User] --> GW[Gateway API]
  GW --> ORCH[Orchestrator]
  ORCH --> POLICY[Policy Engine]
  ORCH --> SLM[SLM Service]
  ORCH --> MEM[Memory Gateway]
  ORCH --> KAFKA[(Kafka)]
  subgraph Observability
    PROM[(Prometheus)]
    LOKI[(Loki)]
  end
  GW --> PROM
  ORCH --> PROM
  SLM --> PROM
  GW --> LOKI
  ORCH --> LOKI
  SLM --> LOKI
```

### Data Flow
```mermaid
%% See docs/diagrams/Data_Flow.mmd for source
flowchart TB
  subgraph Edge
    GW[Gateway API]
  end
  subgraph Core
    ORCH[Orchestrator]
    SLM[SLM Service]
    MEM[Memory Gateway]
  end
  KAFKA[(Kafka)]
  PROM[(Prometheus)]
  LOKI[(Loki)]

  GW --> ORCH
  ORCH --> SLM
  ORCH --> MEM

  ORCH --> KAFKA
  GW --> KAFKA

  SLM --> PROM
  ORCH --> PROM
  GW --> PROM

  GW --> LOKI
  ORCH --> LOKI
  SLM --> LOKI
```
