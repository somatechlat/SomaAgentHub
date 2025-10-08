⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Save this EVERYWHERE at the start of every document!

# Sprint 0 – Framework Integration (Parallel Track B)

**Date:** October 8, 2025  
**Owner:** Framework Strike Team  
**Scope:** Land the first wave of multi-framework adapters inside Temporal and document what is truly complete vs. still pending.

---

## 1. Sprint 0 Outcome

| Item | File(s) | Status | Notes |
|------|---------|--------|-------|
| AutoGen adapter | `services/orchestrator/app/integrations/autogen_adapter.py` | ✅ Implemented | Handles agent config validation, termination keywords, transcript serialization. No automated tests yet. |
| CrewAI adapter | `services/orchestrator/app/integrations/crewai_adapter.py` | ✅ Implemented | Supports manager/workers/tasks. Defaults to sequential process. Lacks retry/backoff and metrics plumbing. |
| LangGraph adapter | `services/orchestrator/app/integrations/langgraph_adapter.py` | ✅ Implemented | Compiles dynamic graphs, wraps handlers/conditions. Requires defensive tooling for async conditions and richer logging. |
| A2A message adapter | `services/orchestrator/app/integrations/a2a_adapter.py` | ✅ Implemented | Bridges Temporal workflows with in-house `A2AProtocol`. Registry is in-memory only. |
| Framework router | `services/orchestrator/app/core/framework_router.py` | ✅ Implemented | Detects `group_chat`, `task_delegation`, `state_machine_routing`, `a2a`. No override flag or accuracy tests. |
| Unified workflow | `services/orchestrator/app/workflows/unified_multi_agent.py` | ✅ Implemented | Calls policy, routes to adapters, emits audit event. Returns `activity`/`pattern` fields (not `framework_used`). |
| Adapter tests | `tests/...` | ❌ Missing | No pytest coverage; all validation is manual. |
| Benchmarks / metrics | `scripts/...` | ❌ Missing | No benchmark scripts or telemetry hooks. |
| Documentation | `docs/INTEGRATION_ARCHITECTURE.md` | ✅ Updated | Reflects the real code paths as of Oct 8, 2025. |

Sprint 0 delivered functional adapters and routing enough to unblock integration consumers. Quality guardrails (tests, telemetry, retries, benchmarks) are still open work.

---

## 2. Highlights from the Codebase

- **Pattern coverage:** All adapters share a consistent payload contract (`agents`, `manager`/`workers`, `graph`, `target_agent_id`) and return normalized dictionaries that the unified workflow forwards to callers.
- **Router behavior:** `FrameworkRouter` now raises explicit `ValueError` for unsupported explicit patterns and defaults to `group_chat` when payloads are ambiguous.
- **Temporal workflow:** `UnifiedMultiAgentWorkflow` keeps a single router instance, evaluates policy through `PolicyEvaluationContext`, and logs dispatch decisions. Audit events only record `activity` name.
- **A2A protocol:** `A2AProtocol` and `AgentRegistry` live under `app/core`, but registry persistence and discovery filtering remain minimal.

---

## 3. Gaps & Follow-Up Work

| Area | Gap | Proposed Action |
|------|-----|-----------------|
| Testing | No unit/integration tests for any adapter or router path. | Build pytest suites using Temporal test harness; cover happy paths and validation errors. |
| Error handling | CrewAI adapter surfaces raw exceptions; router lacks resilience to malformed payloads. | Wrap framework-specific exceptions; add payload validation before dispatch. |
| Telemetry | Activities emit no metrics or traces; Sprint A observability cannot hook in yet. | Add tracing hooks once Track A delivers `somatrace.tracing`. Until then, log structured metadata. |
| Configuration | Adapter defaults are hard-coded (models, timeouts). | Introduce settings modules or environment overrides; document expected env vars. |
| Benchmarks | No reproducible performance numbers. | Create `scripts/framework_bench/*.py` once tests exist to avoid duplicated work. |
| Documentation | How-to guides for adapters are missing beyond architecture doc. | Author `docs/implementation/FRAMEWORK_ADAPTERS_README.md` after tests land. |

---

## 4. Updated Success Criteria

**Completed in Sprint 0**
- ✅ AutoGen, CrewAI, LangGraph, and A2A activities callable from Temporal workers.
- ✅ Unified workflow dispatches to the correct activity for implemented patterns.
- ✅ Documentation in `INTEGRATION_ARCHITECTURE.md` matches production code.

**Outstanding before we call Track B complete**
- ☐ Automated tests with Temporal test environment for every adapter and router branch.
- ☐ Retry/backoff strategies codified per framework (especially CrewAI long-running tasks).
- ☐ Telemetry placeholders (`init_tracing`, cost metadata) wired to satisfy Track A hand-off.
- ☐ Benchmark data captured and published in `docs/implementation/FRAMEWORK_BENCHMARKS.md`.
- ☐ Fallback handling for unsupported/unknown patterns with customer-friendly responses.

---


## 5. Deliverables Checklist (Live State)

- [x] AutoGen adapter implemented and callable from Temporal workers.
- [x] CrewAI adapter implemented and callable from Temporal workers.
- [x] LangGraph adapter implemented and callable from Temporal workers.
- [x] A2A message adapter implemented.
- [x] `FrameworkRouter` selects adapters for all supported patterns.
- [x] `unified-multi-agent-workflow` routes through policy → adapter → audit.
- [ ] Automated tests for adapters, router, and workflow.
- [ ] Telemetry/metrics plumbing aligned with Track A strategy.
- [ ] Benchmark scripts and published results.
- [ ] Developer-facing adapter guide.

---

## 6. Risk Register & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Framework API drift (breaking changes) | High | Pin versions, add smoke tests once coverage exists, watch release notes. |
| Token cost spikes during manual testing | Medium | Favor `gpt-4o-mini`, throttle concurrency, capture cost telemetry once Track A is ready. |
| CrewAI long-running tasks timing out | Medium | Define heartbeat/reporting strategy before enabling retries. |
| Router misclassification | Medium | Collect real requests, expand heuristics, add override flag. |
| Lack of automated tests | High | Prioritize pytest coverage to prevent regressions before onboarding more patterns. |

---

## 7. Exit Criteria to Close Track B

- ☐ `unified-multi-agent-workflow` tested end-to-end across all adapters via automated suite.
- ☐ Router accuracy validated against captured request matrix.
- ☐ Benchmark summary committed to `docs/implementation/FRAMEWORK_BENCHMARKS.md` with reproducible scripts.
- ☐ Telemetry hooks in place for policy decisions, adapter dispatch, and framework outcomes.
- ☐ Knowledge transfer completed (developer guide + runbook).

---

## 8. Next Steps

1. Stand up pytest coverage for each adapter (happy path, validation errors, framework failures).
2. Design retry/backoff policies per adapter and codify them in the unified workflow.
3. Coordinate with observability track on tracing hook contract; add lightweight logging in the interim.
4. Draft developer documentation once tests verify adapter payloads and outputs.
5. Revisit router heuristics with real request samples to ensure pattern detection accuracy.
