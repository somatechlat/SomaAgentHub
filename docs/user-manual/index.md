# User Manual

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Overview

SomaAgentHub is an enterprise-grade orchestration platform for autonomous agents. This manual covers installation, configuration, and usage of the platform's core features.

## What You'll Learn

- [Installation](installation.md) - Deploy SomaAgentHub locally or in production
- [Quick Start Tutorial](quick-start-tutorial.md) - Get up and running in minutes
- [Features](features/) - Detailed feature documentation
- [FAQ](faq.md) - Common questions and troubleshooting

## Core Capabilities

### Multi-Agent Orchestration
Coordinate multiple specialized agents through Temporal workflows with automatic retry and compensation logic.

### Wizard-Driven Workflows
Launch complex agent workflows through guided multi-step processes via the Gateway API.

### Memory & Context Management
Persistent agent memory using vector storage (Qdrant) and real-time context sharing via Redis.

### Policy & Governance
Rule-based guardrails and compliance enforcement through the dedicated Policy Engine.

### Production Infrastructure
Kubernetes-native deployment with Helm charts, health probes, and comprehensive observability.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│             SomaAgentHub                │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Gateway API  │  │ Policy Engine│     │
│  │   (10000)    │  │   (10020)    │     │
│  └──────┬───────┘  └──────┬───────┘     │
│         │                 │              │
│  ┌──────────────────────────────────┐    │
│  │       Orchestrator (10001)       │    │
│  │   Temporal Workflows & Sessions  │    │
│  └──────────────────────────────────┘    │
│                │                          │
│  ┌──────────────────────────────────┐    │
│  │      Memory Gateway (10021)      │    │
│  │   Vector + KV Recall for Agents  │    │
│  └──────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Getting Help

- Check the [FAQ](faq.md) for common issues
- Review [Technical Manual](../technical-manual/) for deployment details
- See [Development Manual](../development-manual/) for contribution guidelines