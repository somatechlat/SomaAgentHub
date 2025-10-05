⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaGent Platform Architecture & Roadmap
_Date: 2025-10-04_

> **SomaGent Real-World Principle:** HERE IN THIS PROJECT WE DON'T MOCK, WE DON'T MIMIC, WE DON'T BYPASSWE ONLY USE REAL DATA, REAL SERVERS, REAL-WORLD SOFTWARE.

## Table of Contents
- [1. Executive summary](#1-executive-summary)
- [2. Platform requirements](#2-platform-requirements)
  - [2.1 Functional goals](#21-functional-goals)
  - [2.2 Non-functional constraints](#22-non-functional-constraints)
  - [2.3 Design principles](#23-design-principles)
- [3. Reference architecture](#3-reference-architecture)
  - [3.1 High-level topology](#31-high-level-topology)
  - [3.2 Control plane & workflow orchestration](#32-control-plane--workflow-orchestration)
  - [3.3 Eventing & messaging](#33-eventing--messaging)
  - [3.4 Data & storage](#34-data--storage)
  - [3.5 Identity, policy & security](#35-identity-policy--security)
  - [3.6 Agent runtime & tooling](#36-agent-runtime--tooling)
  - [3.7 Observability & operations](#37-observability--operations)
  - [3.8 Developer experience & automation](#38-developer-experience--automation)
- [4. Key end-to-end flows](#4-key-end-to-end-flows)
  - [4.1 Tenant session orchestration](#41-tenant-session-orchestration)
  - [4.2 Capsule marketplace lifecycle](#42-capsule-marketplace-lifecycle)
  - [4.3 Observability & disaster recovery loop](#43-observability--disaster-recovery-loop)
- [5. Implementation roadmap (OSS-first)](#5-implementation-roadmap-oss-first)
- [6. Integration & compliance matrix](#6-integration--compliance-matrix)
- [7. Risks, mitigations & open questions](#7-risks-mitigations--open-questions)
- [8. Immediate next actions](#8-immediate-next-actions)
- [Appendix A: Service responsibility map](#appendix-a-service-responsibility-map)
- [Appendix B: Machine-readable summary](#appendix-b-machine-readable-summary)

---

## 1. Executive summary
SomaGent is a constitutionally-governed, multi-tenant agent platform. The server must coordinate complex, long-running agent workflows; ingest millions of concurrent events; and expose auditable APIs that align with KAMACHIQ autonomy goals. This document codifies the production architecture and roadmap using best-in-class open-source software (OSS) so we ship quickly without rebuilding foundational infrastructure.

Highlights:
- **Temporal + Kafka** anchor reliable orchestration for conversational and background workloads.
- **Keycloak + OPA** deliver centralized identity and policy enforcement that every service consumes.
- **PostgreSQL, Redis, Qdrant, ClickHouse** compose a layered data plane supporting transactional, cache, vector, and analytical workloads.
- **SomaSuite Observability Console** (Prometheus metrics, Tempo traces, Loki logs) provides end-to-end visibility with automated chaos and load testing.
- **Marketplace, capsule, and billing flows** run on Temporal-based pipelines with Postgres/MinIO persistence, producing audit streams and cost telemetry.

## 2. Platform requirements
### 2.1 Functional goals
- Coordinate persona-based agent sessions with policy enforcement and memory integration.
- Provide capsule lifecycle management (author  review  publish  install  audit).
- Offer centralized marketplace APIs and admin tooling for capsules, personas, tools, and billing.
- Stream millions of agent/tool events with deterministic replay and real-time analytics.
- Support training mode, governance approvals, and budget controls per tenant.

### 2.2 Non-functional constraints
- **Scale**: Handle >10M daily agent messages, >100K concurrent sessions, and bursty workloads.
- **Reliability**: Target 99.9% service availability; no single point of failure.
- **Security & compliance**: Enforce zero-trust, SOC2-ready audit trails, signed artifacts, and tenant isolation.
- **Observability**: Full metrics/tracing/log coverage with automated anomaly detection.
- **Portability**: Kubernetes-native deployments with GitOps, IaC, and reproducible pipelines.

### 2.3 Design principles
- OSS-first: prefer permissive licenses (Apache, MIT, MPL) with proven production adoption.
- Event-driven: state transitions captured via Kafka topics and persisted for replay/audit.
- Declarative infrastructure: Helm + Argo CD manage environment parity from dev to prod.
- API-first: OpenAPI/gRPC definitions generate SDKs for CLIs, bots, and integrations.
- Defense-in-depth: layered identity, policy, secret management, and runtime hardening.

## 3. Reference architecture
### 3.1 High-level topology
```
                           +----------------------+
                           |   Admin / UI / CLI   |
                           +----------+-----------+
                                      |
                                 (Keycloak)
                                      |
+-------------+       +---------------v----------------+       +--------------------+
|   Clients   |-----> |    API Gateway (Kong/Envoy)    | ----> |   Service Mesh     |
+-------------+       +---------------+----------------+       +----+---------------+
                                    mTLS & OPA                 |    |
                                                               |    |
                                                   +-----------v----v----------------+
                                                   |      Microservices Layer        |
                                                   | (gateway-api, orchestrator, ...) |
                                                   +-----------+----+----------------+
                                                               |    |
                                                               |    |
                                               +---------------+    +-------------------+
                                               | Temporal Workflows | NATS JetStream    |
                                               +---------------+----+-------------------+
                                                               |
                                            +------------------v------------------+
                                            |     Kafka / Streams Backbone        |
                                            +------------------+------------------+
                                                               |
                               +-------------------------------+------------------------------+
                               |                              Data Plane                      |
                               |  Postgres | Redis | Qdrant | ClickHouse | MinIO | OpenSearch  |
                               +--------------------------------+-----------------------------+
                                                              |
                                          +-------------------v-------------------+
                                          | Observability (Prometheus, Tempo, ...)|
                                          +----------------------------------------+
```

### 3.2 Control plane & workflow orchestration
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| Conversational & agent workflows | **Temporal** | Stateful orchestration, retries, signals, versioning | Python SDK for orchestrator service; workers deployed per domain (sessions, capsules, training) |
| Batch/data DAGs | **Argo Workflows** | Kubernetes-native DAG execution for analytics, ML, nightly jobs | GitOps-managed via Argo CD; triggers from Kafka or schedules |
| Task distribution | **Ray** | Executes compute-heavy tasks (SLM inference, embeddings) | Temporal workers enqueue Ray tasks using Ray Serve APIs |
| Lightweight jobs | **Celery + Redis** | Email notifications, cache refresh, housekeeping | Shared library to standardize task registration |
| API ingress | **Kong Gateway OSS** (or Envoy) | JWT validation with Keycloak, rate limiting, request context propagation | Declarative configuration stored in Git; integrates with OPA for inline policy |

### 3.3 Eventing & messaging
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| Core event backbone | **Apache Kafka** (Strimzi operator) | Topics for `slm.requests`, `agent.audit`, `policy.decisions`, `billing.events` | Schema registry (Apicurio) enforces Avro/JSON schemas; Kafka Connect for external sinks |
| Stream processing | **Kafka Streams** / **Apache Flink** | Token aggregation, anomaly detection, SLA monitoring | Flink jobs deployed via Kubernetes operator; results pushed to ClickHouse and Redis |
| Low-latency control | **NATS JetStream** | Pub/sub for Temporal signals, UI notifications, cache invalidation | Lightweight clients in gateway/orchestrator services |

### 3.4 Data & storage
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| Transactional DB | **PostgreSQL** (Timescale/Citus) | Tenants, personas, capsules, billing, audit logs | Logical replication to analytics warehouse; row-level security per tenant |
| Cache & locks | **Redis** | Constitution hash, rate limits, Temporal workflow locks | Redis Sentinel/Cluster for HA |
| Vector search | **Qdrant** | Embedding store for memory RAG, persona retrieval | gRPC + API access; background sync to MinIO snapshots |
| Analytics warehouse | **ClickHouse** | High-volume metrics, billing ledgers, success/failure trends | Kafka engine tables ingest events directly |
| Object storage | **MinIO** | Capsule bundles, persona artifacts, DR exports | Versioned buckets with Cosign signatures |
| Search | **OpenSearch** | Indexed transcripts, runbooks, log enrichment | Federated search for admin console |

### 3.5 Identity, policy & security
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| Identity provider | **Keycloak** | OAuth/OIDC, SAML, SCIM, multi-factor | Realm per environment; service accounts for microservices |
| Policy enforcement | **Open Policy Agent (OPA)** + **OpenFGA** | Rego policies + relationship-based auth | Sidecar or Envoy external authorization; policy bundles stored in Git |
| Secrets & key management | **HashiCorp Vault** | Dynamic DB credentials, signing keys, capsule attestation | Vault Agent injectors for services; PKI for mTLS |
| Supply chain | **Sigstore Cosign** | Sign container images and capsule artifacts | Verify during deployment pipeline |
| Runtime security | **Falco** / **Kyverno** | Runtime detection and policy enforcement | Kyverno validates admissions; Falco emits alerts into Kafka |

### 3.6 Agent runtime & tooling
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| SLM serving | **vLLM** or **Text Generation Inference** | Serve open LLMs with efficient batching and streaming | Ray cluster can host inference; adapters for third-party APIs via LangChain wrappers |
| Tool adapters | **Airbyte OSS**, **Playwright** containers, **gRPC** tool interface | Integrate SaaS APIs, UI interactions, CLI containers | Temporal workflows mount tool containers; audit each invocation |
| Feature flags | **OpenFeature** + **Flagd** | Safely roll out agent behaviors and UI features | Config stored in Git; evaluation at gateway/orchestrator |
| Marketplace backend | SomaGent `task-capsule-repo` + **Hasura GraphQL Engine** | CRUD API for capsules, submissions, installations | Hasura auto-generates GraphQL; fine-grained auth via JWT claims |

### 3.7 Observability & operations
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| Metrics | **Prometheus** + **Thanos** | Scrape microservices, Ray, Kafka, Temporal; long-term storage | Helm charts with service monitors; tenant labels for dashboards |
| Tracing | **Tempo** / **Jaeger** | OpenTelemetry traces across gateway, workflows, workers | Instrument Python/Go services with OTEL SDK |
| Logs | **Loki** | Centralize structured logs with correlation IDs | Promtail sidecars attach tenant/session metadata |
| Dashboards & alerts | **SomaSuite Observability Console** + **Alertmanager** | Agent One Sight, capsule KPIs, budget alerts | Alert policies push to PagerDuty/Slack |
| Chaos & load | **LitmusChaos**, **k6**, **Gremlin OSS** | Automate DR drills, load tests, and failure injections | Results streamed to Kafka and analytics service |

### 3.8 Developer experience & automation
| Concern | Technology | Role | Integration notes |
|---------|------------|------|-------------------|
| CI/CD | **Dagger** + **GitHub Actions** | Reproducible builds/tests/deploys | Dagger pipelines invoke unit/integration tests, sign images, push to registry |
| GitOps | **Argo CD** | Declarative deployment to Kubernetes clusters | Enforce drift detection and automated rollbacks |
| Developer portal | **Backstage** | Central catalog of services, docs, runbooks, integrations | Plugins for Temporal, Kafka topics, capsule inventory |
| Local dev | **Tilt** / **Skaffold** | Rapid inner-loop sync with Kubernetes parity | Encourages consistent dev environment |
| Quality & security | **SonarQube**, **Trivy**, **Semgrep** | Static analysis, container scanning, SAST | Integrated into CI gating |

## 4. Key end-to-end flows
### 4.1 Tenant session orchestration
1. Client authenticates via Keycloak; JWT includes tenant, persona, capability claims.
2. Kong gateway validates JWT, checks OPA policy for route/tenant permissions, and forwards to `gateway-api`.
3. `gateway-api` invokes Temporal workflow `session.start` with request context.
4. Workflow fetches constitution hash (Redis) and verifies policy compliance via OPA/OpenFGA.
5. Workflow persists session metadata to Postgres, emits `agent.audit.started` to Kafka.
6. Workflow enqueues SLM job to Ray cluster (`slm.requests` topic or direct Ray Serve call); streaming responses forwarded to client via WebSocket.
7. Tool invocations run in sandboxed containers (Kubernetes jobs) with outputs stored in MinIO and logged via Kafka.
8. Upon completion, workflow records summaries in ClickHouse, updates Qdrant memory, and posts `agent.audit.completed`.

### 4.2 Capsule marketplace lifecycle
1. Capsule author submits bundle via GraphQL (Hasura) or CLI; artifact stored in MinIO, metadata in Postgres.
2. Temporal `capsule.review` workflow triggers: scans artifact (Trivy), validates signatures (Cosign), runs automated policy checks (OPA).
3. Reviewers receive notifications (NATS) and approve/reject via admin UI. Decision recorded in Postgres and Kafka (`capsule.moderation`).
4. On approval, workflow publishes to marketplace index, generates installation manifests, and updates Backstage catalog.
5. Tenant installation triggers `capsule.install` workflow: applies policy templates, provisions schedules in Temporal, syncs Qdrant embeddings, and emits billing seed events.
6. Billing service aggregates runtime usage (Kafka Streams) and posts ledger entries to ClickHouse/Postgres; analytics service updates dashboards.

### 4.3 Observability & disaster recovery loop
1. LitmusChaos orchestrates fault injection (e.g., Kafka broker failover) on schedule via Argo Workflows.
2. Metrics, traces, and logs capture impact; Alertmanager validates SLO alerting.
3. Temporal `drill.record` workflow writes results to Postgres and analytics service via `/v1/drills/disaster` API.
4. Analytics service pushes notifications and updates DR dashboards; results stored in ClickHouse for trend analysis.

## 5. Implementation roadmap (OSS-first)
| Phase | Timeline | Focus | Key deliverables | Dependencies |
|-------|----------|-------|------------------|--------------|
| **0. Foundations** | Weeks 00 | Bootstrap infra (Kafka, Temporal, Postgres, Redis, Keycloak, Prometheus) via Helm/Argo CD; set up Dagger CI/CD. | Cluster manifests, GitOps repos, baseline metrics/logs, CI pipeline with scanning. | Kubernetes cluster, registry access |
| **1. Core orchestration** | Weeks 26 | Replace service stubs with Temporal workflows; integrate OPA, Keycloak, Ray; implement session lifecycle and policy enforcement. | `session.start` workflow, policy evaluation service, Ray-backed SLM stub, audit topics. | Phase 0 complete |
| **2. Marketplace & analytics** | Weeks 60 | Implement capsule submission/review/install flows; deploy Hasura; build analytics service ingestion (Kafka  ClickHouse). | Marketplace GraphQL API, Temporal workflows, billing ledger, dashboards v1. | Phase 1 complete |
| **3. Hardening & scale** | Weeks 104 | Introduce chaos/load harness, Thanos/Tempo, Vault secrets, Cosign signing, multi-region Postgres replicas. | Automated DR drills, signed artifacts, RPO/RTO dashboards, policy regression suite. | Phases 12 |
| **4. Autonomy & expansion** | Weeks 140 | Launch KAMACHIQ orchestration (multi-agent DAGs), extend tool adapters, enable capsule marketplace monetization options, finalize compliance runbooks. | Multi-agent Temporal workflows, tool sandbox policies, marketplace billing integration, SOC2 evidence packages. | Prior phases |

## 6. Integration & compliance matrix
| Component | License | Maturity | Operations notes | Compliance considerations |
|-----------|---------|----------|------------------|---------------------------|
| Temporal | Apache 2.0 | GA, widely adopted | Requires Cassandra/MySQL/Postgres persistence; Helm chart available | Workflow history retention policies, encrypted persistence |
| Apache Kafka | Apache 2.0 | GA | Strimzi operator handles brokers/ZKless KRaft | Enable TLS/mTLS, ACLs per service account |
| Keycloak | Apache 2.0 | GA | Use Keycloak Operator; configure realm backups | Enforce MFA, auditing, integrate with corporate IdP |
| OPA | Apache 2.0 | GA | Bundle policies in Git; use OPA sidecars or Envoy authz | Versioned policies with approvals |
| Ray | Apache 2.0 | GA | Deploy via KubeRay operator; autoscale worker pods | Ensure resource quotas, sandbox network access |
| Prometheus/Thanos | Apache 2.0 | GA | Thanos for long-term storage; feed SomaSuite Observability Console | Metric retention and PII scrubbing |
| Tempo/Loki | AGPLv3 / AGPLv3 | GA | Deploy via Helm; integrate with Promtail/OTEL | Control access to logs/traces with tenant scoping |
| MinIO | AGPLv3 | GA | Deploy in distributed mode; lock-down IAM policies | Encrypt at rest, version artifacts |
| Hasura | Apache 2.0 | GA | Run GraphQL engine with Postgres; metadata in Git | Enforce row-level security, JWT claims mapping |
| Backstage | Apache 2.0 | GA | Deploy as Node service; plugin ecosystem | Integrate SSO, limit sensitive catalog data |

## 7. Risks, mitigations & open questions
| Risk | Impact | Mitigation | Owner |
|------|--------|-----------|-------|
| Temporal scaling misconfiguration | Workflow latency, backlogs | Use Temporal visibility metrics, set shard counts, load-test with k6 | Platform team |
| Kafka topic proliferation | Operational overhead, retention cost | Establish topic governance, use Schema Registry, enforce lifecycle policies | Data platform |
| Policy drift between services | Security gaps | Centralize policies in Git, automated OPA bundle validation CI, policy regression testing | Security/Platform |
| Marketplace compliance | Exposure to unvetted capsules | Automated scans (Trivy, Semgrep), manual review gating, attestation logging | Marketplace lead |
| Ray resource exhaustion | SLM outages | Autoscaling, resource quotas, fallback providers | AI runtime |
| Multi-tenancy data leakage | Regulatory breach | Row-level security, tenant-scoped encryption keys, continuous audit trails | Data platform |

Open questions:
1. Which managed cloud offerings (if any) will supplement OSS (e.g., managed Kafka vs self-hosted)?
2. Do we require FIPS-validated cryptography for certain tenants?
3. How will monetization of the capsule marketplace integrate with external billing providers (Stripe, Paddle)?
4. What level of offline/edge support is required for capsules/tools?

## 8. Immediate next actions
1. Stand up Temporal + Cassandra or Temporal + Postgres (production recommended) and scaffold first `session.start` workflow.
2. Integrate Keycloak & OPA into `gateway-api` and `orchestrator` services (JWT validation + policy check middleware).
3. Provision Strimzi Kafka cluster with baseline topics and Schema Registry.
4. Configure Prometheus, Loki, and Tempo pipelines for the existing services and wire them into the SomaSuite Observability Console to establish the baseline dashboards.
5. Author API/GraphQL schema for capsule marketplace and align with Hasura metadata plan.

### Parallel Sprint Activation (Approved 2025-10-04)
- Sprint 2 (Governance Core) and Sprint 3 (Runtime & Training Slice) plans are approved and now captured in `docs/sprints/Sprint-2.md` and `docs/sprints/Sprint-3.md` under newly added **Implementation Plan** sections.
- Run both sprints in parallel per the Parallel Sprint Execution Playbook; governance squad leads Sprint 2 while runtime squad leads Sprint 3 with shared integration checkpoints every 48 hours.
- Gateway, policy engine, identity, orchestrator, and training features must integrate continuously—follow the integration test scaffolds defined in the sprint docs to keep environments in lockstep.

## Appendix A: Service responsibility map
| Service | Core responsibilities | Primary dependencies | Key outputs |
|---------|----------------------|----------------------|-------------|
| `gateway-api` | Public API facade, request validation, session initiation | Keycloak, OPA, Temporal | Session workflow triggers, audit events |
| `orchestrator` | Manages agent conversation workflows, tool orchestration, policy enforcement | Temporal, Ray, Redis, Qdrant | Agent state updates, tool execution requests |
| `policy-engine` | Evaluate constitutional and tenant policies, score actions | OPA bundle store, Postgres | Policy verdicts, audit logs |
| `identity-service` | Tenant/user management, integration with Keycloak | Keycloak Admin API, Postgres | User provisioning events, token issuance orchestration |
| `settings-service` | Tenant configuration, model profiles, feature toggles | Postgres, OpenFeature | Settings change events, config snapshots |
| `slm-service` | Interface to language models, token accounting | Ray/vLLM, ClickHouse, Kafka | Responses, token metrics |
| `task-capsule-repo` | Capsule metadata, submissions, review workflows | Postgres, MinIO, Temporal | Capsule manifests, marketplace feeds |
| `analytics-service` | Capsule KPIs, billing analytics, anomaly detection | ClickHouse, Kafka Streams | Dashboards, anomaly alerts |
| `memory-gateway` | Read/write SomaBrain/Stubs, vector search routing | Qdrant, Redis, Postgres | Memory retrieval responses |
| `billing-service` | Subscription plans, ledger aggregation, billing exports | Postgres, ClickHouse, Kafka | Billing ledgers, alerts |
| `tool-service` | Tool registry, sandbox orchestration, adapter lifecycle | Kubernetes jobs, Airbyte/Playwright | Tool execution results, audit trails |
| `recall-service` (future) | Long-term memory replay and summarization | Qdrant, MinIO | Summaries, embeddings |

## Appendix B: Machine-readable summary
```yaml
soma_gent:
  version: "2025-10-04"
  principles:
    - oss_first
    - event_driven
    - zero_trust
    - api_first
  control_plane:
    workflows:
      engine: temporal
      batch_engine: argo_workflows
      workers:
        heavy_compute: ray
        lightweight: celery
    ingress:
      gateway: kong
      service_mesh: istio
  messaging:
    backbone: kafka
    stream_processing:
      - kafka_streams
      - flink
    low_latency_bus: nats_jetstream
  data_plane:
    relational: postgres
    cache: redis
    vector: qdrant
    analytics: clickhouse
    object_storage: minio
    search: opensearch
  identity_security:
    idp: keycloak
    policy: opa
    relationship_acl: openfga
    secrets: vault
    supply_chain: cosign
  agent_runtime:
    slm_serving: vllm
    tool_adapters:
      - airbyte
      - playwright
      - grpc_custom
    feature_flags: openfeature
    marketplace_api: hasura_graphql
  observability:
    metrics: prometheus
    tracing: tempo
    logs: loki
  dashboards: somasuite_observability_console
    automation:
      chaos: litmus
      load: k6
  devops:
    cicd:
      orchestrator: dagger
      runner: github_actions
    gitops: argo_cd
    developer_portal: backstage
    security_scans:
      - trivy
      - semgrep
      - sonarqube
  roadmap:
    phases:
      - name: foundations
        focus: infra_bootstrap
      - name: core_orchestration
        focus: workflows_policy
      - name: marketplace_analytics
        focus: capsule_lifecycle
      - name: hardening_scale
        focus: chaos_security
      - name: autonomy_expansion
        focus: kamachiq_multi_agent
```

---

## 9. Task Capsule Architecture (Detailed)

### 9.1 Philosophy: Dynamic Agent Composition
SomaGent does **not** maintain a zoo of permanent agents. Instead, we use **Task Capsules** — portable, versioned packages that describe complete jobs with persona templates, tool stacks, memory snapshots, and guardrails. The orchestrator instantiates capsules on-demand, creating ephemeral agent instances that dissolve after completion.

**Why Capsules beat "lots of agents":**
- **Scale** – Launch thousands of capsule instances in parallel without overhead of persistent processes
- **Updatability** – Modify capsule template once, all future runs benefit instantly
- **Marketplace ready** – Capsules become shareable marketplace assets
- **Explainability** – Versioned like code, easy to audit execution history

### 9.2 Capsule Lifecycle States

```
Authoring → Storage → Discovery → Installation → Instantiation → Execution → Completion → Learning
```

**Key Benefits:**
1. Reusable across projects
2. Version-controlled and auditable
3. Marketplace-ready for sharing
4. Constitutional compliance enforced
5. Self-improving via execution metrics

---

## 10. KAMACHIQ Autonomous Mode

### 10.1 Vision
KAMACHIQ mode enables fully autonomous project execution with minimal human intervention.

**Autonomy Levels:**
- Level 1: Supervised (human approves each step)
- Level 2: Semi-Autonomous (approval for high-risk only)
- Level 3: Autonomous (review at milestones)
- Level 4: KAMACHIQ (fully autonomous + self-improvement)

**Safety Mechanisms:**
- Constitutional enforcement at every step
- Budget limits with automatic pause
- Human override and kill switch
- Complete audit trail

### 10.2 KAMACHIQ Execution Phases

1. **Intent Capture** - Parse high-level request
2. **Planning** - Decompose into deliverables
3. **Workspace Provisioning** - Setup Git/tools/boards
4. **Parallel Execution** - Multi-capsule orchestration
5. **Review & Integration** - Quality gates
6. **Deployment** - Staging → Production
7. **Knowledge Sync** - Update SomaBrain
8. **Self-Improvement** - Analyze and optimize

---

## 11. Deployment Modes

| Mode | Use Case | Training | Enforcement |
|------|----------|----------|-------------|
| developer-light | Quick spikes | Enabled | Permissive |
| developer-full | Integration testing | Opt-in | Relaxed |
| test | CI pipelines | Frozen | Deterministic |
| staging | Pre-prod validation | Admin-controlled | Production-like |
| production | Live deployment | Closed | Strict |

**State Synchronization:**
- Transactional outbox pattern for events
- RPO: <1 minute, RTO: <15 minutes
- Exactly-once message delivery

---

## 12. Reference Documentation

**Architecture:** CANONICAL_ROADMAP.md, KAMACHIQ_Mode_Blueprint.md, SomaGent_Security.md  
**Development:** Gap_Analysis_Report.md, Implementation_Roadmap.md, Developer_Setup.md  
**Operations:** runbooks/{disaster_recovery, constitution_update, kamachiq_operations}.md  
**Sprints:** sprints/{Parallel_Backlog, Parallel_Wave_Schedule, Command_Center}.md

---

**Last Updated:** October 4, 2025  
**Status:** Living Document (bi-weekly review)  
**Maintained By:** Architecture Team
