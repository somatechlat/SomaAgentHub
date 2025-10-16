# SomaAgentHub 2.5 Roadmap

This roadmap captures the end-to-end plan for delivering the "Perfect SomaAgentHub" platform. Each phase records the Adopt/Adapt/Build strategy, the official upstream dependencies involved, and the expected outcomes. Progress should only advance once the prior phase is production ready (tests, documentation, observability, rollbacks).

---

## Phase 1 – Harden the Core
- Adopt only official base images (pin digests, document provenance) for all service and infra containers.
- Extend CI to run Trivy scans, generate SBOMs (Syft/Grype), and fail on critical CVEs.
- Introduce Vault + External Secrets for runtime configuration; migrate identity/gateway secrets off environment files.
- Deploy observability foundation: OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana. Ensure every service exports metrics/logs/traces.
- Expand local & cluster deployments to include PostgreSQL (app data), Qdrant, Kafka (Strimzi) → ClickHouse, MinIO with backups.

## Phase 2 – Zero-Trust Network Fabric
- Install Istio service mesh with mutual TLS and traffic policy defaults (timeouts, retries, circuit breaking).
- Front the platform with Envoy Gateway using official images; route all public traffic through ext-authz.
- Integrate OPA for request-time authorization. Evaluate SPIRE for SVID issuance; otherwise rely on Vault-issued certs via Istio SDS.
- Enforce Gatekeeper constraints (non-root, resource limits) and require Cosign-signed images.

## Phase 3 – Governance, Data, and GitOps
- Adopt OpenFGA for relationship-based access control; adapt gateway/orchestrator to consult it.
- Roll out Argo CD for GitOps deployments with signed manifests and promotion waves.
- Build Kafka → ClickHouse audit pipeline; expose Grafana dashboards and alerts for compliance/cost.
- Integrate Kubecost for FinOps visibility.

## Phase 4 – Agent Intelligence & Tooling
- Integrate LangGraph to express deterministic multi-agent workflows inside the orchestrator.
- Adopt CrewAI abstractions (role-based crews, declarative YAML authoring, task routing) and adapt them to compile into LangGraph.
- Adapt AutoGen messaging patterns as an optional conversation toolkit.
- Expand tool service to load RAG providers (LlamaIndex, Haystack) as adapters behind Memory Gateway.

## Phase 5 – Operations Excellence
- Add load and resilience testing (k6, Chaos Mesh) with official images.
- Establish promotion gates (dev → staging → prod) with rollback procedures and audit trails.
- Maintain SBOM inventory, digest refresh automation, and long-term support cadence.

---

### Execution Notes
- Each phase must ship with documentation updates, runbooks, and validation tests.
- Never downgrade security: if a component fails compliance (unsigned image, CVE), block deployment until resolved.
- Track progress in this file by appending dated status sections per phase.
