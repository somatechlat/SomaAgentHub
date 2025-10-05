# Wave C Quick Reference - October 18, 2025 Kickoff 🚀

**3 Simultaneous Sprints | 7 Squads | 6 Weeks to Marketplace Launch**

---

## 📅 Timeline at a Glance

```
Oct 5  ━━━ Infrastructure deployed (Observability stack ready)
Oct 18 ━━━ Wave C Kickoff (Sprint 5+6 start)
Oct 25 ━━━ Sprint 7 starts (Marketplace)
Nov 1  ━━━ Sprint 5 ends (KAMACHIQ demo)
Nov 8  ━━━ Sprint 6 ends (Production live)
Nov 15 ━━━ Sprint 7 ends + Marketplace Launch 🎉
```

---

## 🎯 Three Sprints Overview

### Sprint-5: KAMACHIQ Autonomous Foundation 🧠
**Duration:** Oct 18 - Nov 1 (2 weeks)  
**Lead Squads:** Policy & Orchestration + SLM Execution

**Deliverables:**
- Temporal workflow infrastructure
- Project planning & decomposition algorithm
- Multi-agent orchestration (parallel task execution)
- Quality gates (automated review, approval)
- **Demo:** Simple project executed autonomously

**Success:** Python CLI calculator built end-to-end without human intervention

---

### Sprint-6: Production Hardening 🛡️
**Duration:** Oct 18 - Nov 8 (3 weeks)  
**Lead Squad:** Infra & Ops + All Squads

**Deliverables:**
- ✅ Observability stack (Prometheus, Grafana) - **DEPLOYED OCT 5**
- Chaos engineering (Litmus, failure testing)
- Load testing (k6, 1000 concurrent sessions)
- Security hardening (Vault, mTLS, scanning)
- CI/CD pipeline (GitHub Actions, Argo CD)
- **Production deployment + 7-day burn-in**

**Success:** 99.9% uptime, <500ms P95 latency, zero critical vulnerabilities

---

### Sprint-7: Marketplace & Analytics 🏪
**Duration:** Oct 25 - Nov 15 (3 weeks)  
**Lead Squads:** UI & Experience + Analytics Service

**Deliverables:**
- Task Capsule repository (submit, review, publish workflow)
- Marketplace UI (catalog, search, install)
- Analytics pipeline (ClickHouse, event ingestion)
- Dashboards (platform, user, capsule, admin)
- Token economics (forecasting, billing)
- **Community capsule published and monetized**

**Success:** External user submits, publishes, and earns revenue from capsule

---

## 👥 Squad Assignments

| Squad | Wave C Primary | Wave C Support | Squad Size |
|-------|----------------|----------------|------------|
| **Policy & Orchestration** | Sprint-5 Lead | Sprint-6 support | 4 |
| **SLM Execution** | Sprint-5 Co-Lead | Sprint-6 load testing | 3 |
| **Infra & Ops** | Sprint-6 Lead | All infrastructure | 5 |
| **UI & Experience** | Sprint-7 Lead | Sprint-4 completion | 4 |
| **Memory & Constitution** | Sprint-5 support | Sprint-6 instrumentation | 3 |
| **Identity & Settings** | Sprint-6 support | Sprint-6 Vault/mTLS | 3 |
| **Analytics Service** | Sprint-7 Co-Lead | Sprint-6 metrics | 3 |

**Total:** ~25 engineers across 7 squads

---

## 🔗 Critical Dependencies

### Infrastructure (Week 1: Oct 18-25)
```
Day 1 (Oct 18):
├─ ✅ Observability Stack (DONE Oct 5)
├─ Temporal dev server (local setup)
└─ OpenTelemetry instrumentation (all services)

Day 3 (Oct 21):
├─ First KAMACHIQ workflow executes
├─ First chaos experiment (Kafka failure)
└─ Integration: Temporal → Kafka → SLM

Day 5 (Oct 25):
├─ ClickHouse deployment (Sprint-7)
├─ Vault deployment (Sprint-6)
└─ Load testing baseline
```

### Cross-Sprint Integration
```
Sprint-5 → Sprint-6:
  - Temporal HA for production
  - Workflow load testing

Sprint-5 → Sprint-7:
  - Capsule execution via KAMACHIQ
  - Task dependency resolution

Sprint-6 → Sprint-7:
  - Analytics Kafka topics
  - Capsule signing (Cosign)
  - Marketplace metrics
```

---

## 📊 Already Deployed (Oct 5)

### ✅ Observability Stack
- **Namespace:** `observability`
- **Components:** Prometheus, Grafana, Kube-State-Metrics, Node Exporter
- **Status:** 5/5 pods running
- **Access:** 
  - Grafana: http://localhost:30080 (admin/admin)
  - Prometheus: kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090

### ✅ ServiceMonitors
- 6 ServiceMonitors deployed for auto-discovery
- All SomaAgent services will be automatically scraped
- Labels: `monitoring: enabled` on Kubernetes services

### ✅ Infrastructure
- PostgreSQL, Redis, Kafka/Redpanda running (soma-memory namespace)
- Qdrant vector DB operational
- 6/6 memory services healthy

---

## 📝 Day 1 Actions (Oct 18)

### All Hands Kickoff (09:00 PT)
- [ ] Review Wave C objectives
- [ ] Confirm squad assignments
- [ ] Address questions and blockers

### Immediate Tasks

**Policy & Orchestration (Sprint-5):**
- [ ] Set up Temporal dev server locally
- [ ] Add temporalio SDK to orchestrator
- [ ] Create first workflow module
- [ ] Test "hello world" workflow

**Infra & Ops (Sprint-6):**
- [ ] Deploy Vault for secrets management
- [ ] Install Litmus for chaos engineering
- [ ] Set up k6 load testing framework
- [ ] Document Grafana dashboard creation

**All Squads (Sprint-6):**
- [ ] Add OpenTelemetry to services (see guide)
- [ ] Verify /health and /metrics endpoints
- [ ] Test metrics in Prometheus
- [ ] Create basic Grafana dashboard

**UI & Experience (Sprint-7 prep):**
- [ ] Design ClickHouse schemas
- [ ] Mockup marketplace UI wireframes
- [ ] Plan capsule submission workflow

---

## 🎯 Week 1 Exit Criteria (Oct 25)

### Sprint-5
- [ ] Temporal running (dev or production)
- [ ] First workflow executes successfully
- [ ] Project decomposition algorithm prototype
- [ ] Agent spawning pattern defined

### Sprint-6
- [ ] All services instrumented with OpenTelemetry
- [ ] Grafana dashboards created
- [ ] First chaos experiment passed
- [ ] Vault deployed, first secrets migrated

### Sprint-7
- [ ] ClickHouse deployed
- [ ] Analytics pipeline ingesting test events
- [ ] Marketplace UI skeleton deployed

---

## 📚 Essential Documents

### Sprint Plans (Detailed)
- [`Sprint-5.md`](Sprint-5.md) - KAMACHIQ (56 tasks, 5 epics)
- [`Sprint-6.md`](Sprint-6.md) - Production (68 tasks, 6 epics)
- [`Sprint-7.md`](Sprint-7.md) - Marketplace (62 tasks, 6 epics)

### Coordination
- [`Parallel_Backlog.md`](Parallel_Backlog.md) - Live task grid
- [`Parallel_Wave_Schedule.md`](Parallel_Wave_Schedule.md) - Milestones
- [`Command_Center.md`](Command_Center.md) - Daily procedures

### Technical Guides
- [`OpenTelemetry_Integration_Guide.md`](../development/OpenTelemetry_Integration_Guide.md) - Instrumentation how-to
- [`Developer_Setup.md`](../development/Developer_Setup.md) - Local dev setup
- [`TEMPORAL_DEPLOYMENT_NOTE.md`](../../infra/helm/TEMPORAL_DEPLOYMENT_NOTE.md) - Temporal strategy

### Progress
- [`Wave_C_Progress_Oct5.md`](Wave_C_Progress_Oct5.md) - Infrastructure status
- [`Wave_C_Launch.md`](Wave_C_Launch.md) - Executive summary

---

## 🚨 Common Pitfalls & Solutions

### "My metrics aren't showing up in Prometheus"
1. Check service has `monitoring: enabled` label
2. Verify `/metrics` endpoint works: `curl localhost:8000/metrics`
3. Check ServiceMonitor: `kubectl get servicemonitor -n observability`
4. Look at Prometheus targets: http://localhost:9090/targets

### "Temporal workflow won't start"
1. Use dev server first: `temporal server start-dev`
2. Check connection: `temporal workflow list`
3. Verify namespace: default is `default`
4. Check workflow is registered in worker

### "Load test is crashing the cluster"
1. Use dedicated namespace with resource quotas
2. Start with 10 users, ramp slowly
3. Monitor with Grafana during test
4. Stop immediately if P95 > 2s

### "ClickHouse deployment failing"
1. Check PVC storage available
2. Reduce replica count for dev (1 instead of 3)
3. Verify namespace has sufficient resources
4. Check logs: `kubectl logs -n observability clickhouse-0`

---

## 📞 Communication Channels

### Daily Standups
- **Time:** 09:00 PT
- **Format:** Round-robin by squad
- **Focus:** Blockers, dependencies, progress

### Integration Day (Every Wednesday)
- **Time:** All day
- **Activities:** Deploy to staging, smoke tests, demos
- **Goal:** Validate cross-squad integration

### Slack Channels
- `#wave-c-coordination` - Cross-squad blockers
- `#sprint-5-kamachiq` - KAMACHIQ development
- `#sprint-6-observability` - Production hardening
- `#sprint-7-marketplace` - Marketplace & analytics
- `#infra-ops` - Infrastructure issues

### Escalation Path
1. Squad lead (immediate blockers)
2. Wave coordinator (cross-squad issues)
3. Engineering leadership (strategic decisions)

---

## 🎉 Success Metrics

### Sprint-5 KPIs
- Workflow execution success rate >95%
- Project decomposition <30 seconds
- Quality auto-approval >70%

### Sprint-6 KPIs
- Service availability 99.9%
- P95 latency <500ms
- Zero high/critical vulnerabilities
- CI/CD pipeline <15 minutes

### Sprint-7 KPIs
- Analytics ingestion 10K events/sec
- Query latency <1 second
- Marketplace search <500ms

### Overall Wave C Success
- ✅ KAMACHIQ demo completes autonomously
- ✅ Production deployed with 7-day burn-in
- ✅ Community capsule published and installed
- ✅ 1000 concurrent session load test passed
- ✅ All integration tests passing

---

## 🎊 Celebration Points

- **Oct 21:** First KAMACHIQ workflow runs! 🤖
- **Oct 28:** First successful load test! 📈
- **Nov 1:** KAMACHIQ demo day! 🎬
- **Nov 8:** Production goes live! 🚀
- **Nov 15:** MARKETPLACE LAUNCH! 🎉🏪

---

**Let's ship this! 💪**

*"We do not mock, we do not imitate - we use MATH, perfect math, and real servers!"*

---

**Last Updated:** October 5, 2025  
**Next Update:** October 18, 2025 (Wave C Kickoff)  
**Questions?** See your squad lead or #wave-c-coordination
