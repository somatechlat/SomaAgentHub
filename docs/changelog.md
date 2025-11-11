# Changelog

![Version](https://img.shields.io/badge/version-1.0.0-blue)

All notable changes to SomaAgentHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-19

### Added
- ISO/IEC compliant documentation structure
- Core services: Gateway API, Orchestrator, Identity Service, Memory Gateway, Policy Engine
- Kubernetes-native deployment with Helm charts
- Temporal workflow orchestration
- FastAPI-based microservices architecture
- Redis session management
- Qdrant vector storage integration
- Prometheus metrics and observability
- Make-based build and deployment automation
- Comprehensive testing framework (unit, integration, e2e)

### Infrastructure
- Kind-based local development environment
- Docker Compose for local dependencies (Temporal, Redis)
- Kubernetes manifests with health probes and resource limits
- Helm chart with environment-aware configuration
- CI/CD pipeline with GitHub Actions

### Services
- **Gateway API** (port 10000): Public ingress and wizard flows
- **Orchestrator** (port 10001): Temporal workflow coordination
- **Identity Service** (port 10002): Token issuance and validation
- **Memory Gateway** (port 10021): Vector and KV storage
- **Policy Engine** (port 10020): Rule-based guardrails
- **Analytics Service**: Metrics collection and analysis
- **Billing Service**: Usage tracking and cost management
- **Tool Service**: External tool integration adapters

### Documentation
- User manual with installation and feature guides
- Technical manual with architecture and runbooks
- Development manual with coding standards and setup
- Onboarding manual for new contributors
- Agent onboarding for AI automation