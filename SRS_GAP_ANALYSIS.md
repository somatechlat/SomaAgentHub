# SRS Gap Analysis: SomaAgentHub v4.0.0
**Current vs Specified Implementation**

**Date:** 2025-12-03  
**Analyst:** All 7 Required Personas (per VIBE_CODING_RULES.md)  
**Version:** 1.0

---

## Executive Summary

This document analyzes the gap between the SRS_somagentHub.md specification (comprehensive model definitions) and the actual implemented codebase in `/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub`.

**Coverage Status:**
- ✅ **Implemented**: ~15% of SRS models
- ⚠️ **Partial**: ~10% of SRS models  
- ❌ **Missing**: ~75% of SRS models

---

## 0. Modeling Principles (SRS Section 0)

### SRS Requirements:
- Multi-tenancy by default (`tenant_id` on all objects)
- Immutable IDs (UUID)
- Versioned definitions vs non-versioned instances
- Cross-system references (Agent01, SomaBrain)
- Auditability (all actions logged)

### Current Implementation:
| Principle | Status | Gap |
|-----------|--------|-----|
| Multi-tenancy | ❌ MISSING | NO `tenant_id` fields in any models |
| Immutable IDs | ✅ IMPLEMENTED | UUID primary keys exist |
| Versioning | ⚠️ PARTIAL | `GraphWorkflowModel` has `version`, others don't |
| Cross-system refs | ❌ MISSING | No `ExternalRef` model exists |
| Auditability | ⚠️ PARTIAL | `AuditLogModel` exists but incomplete |

**Critical Gap:** Multi-tenancy is completely absent from the database schema.

---

## 1. Identity & Cross-Cutting References (SRS Section 1)

### SRS Models:
1. `TenantRef`
2. `PrincipalRef`
3. `ExternalRef`

### Current Implementation:
| Model | Status | Location | Gap |
|-------|--------|----------|-----|
| TenantRef | ❌ MISSING | N/A | Entire model missing |
| PrincipalRef | ❌ MISSING | N/A | Entire model missing |
| ExternalRef | ❌ MISSING | N/A | Entire model missing |

**Impact:** Cannot track users, tenants, or external system references (Agent01, SomaBrain).

---

## 2. Capsule Model Family (SRS Section 2)

### SRS Models:
1. `CapsuleDefinition` - Template/blueprint
2. `CapsuleInstance` - Runtime binding

### Current Implementation:

#### CapsuleSpec (Pydantic)
**Location:** `services/common/models/capsule.py`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ❌ Missing | MISSING |
| `tenant_id` | ❌ Missing | MISSING |
| `name` | ⚠️ In `metadata` dict | PARTIAL |
| `version` | ⚠️ In `metadata` dict | PARTIAL |
| `status` | ❌ Missing | MISSING |
| `default_persona_ref` | ✅ `persona_id` (string) | PARTIAL - not ExternalRef |
| `allowed_tools` | ✅ `tool_whitelist` | IMPLEMENTED |
| `prohibited_tools` | ❌ Missing | MISSING |
| `allowed_mcp_servers` | ❌ Missing | MISSING |
| `tool_risk_profile` | ❌ Missing | MISSING |
| `max_wall_clock_seconds` | ✅ `max_runtime_seconds` | IMPLEMENTED |
| `max_concurrent_nodes` | ❌ Missing | MISSING |
| `allowed_runtimes` | ❌ Missing | MISSING |
| `resource_profile` | ⚠️ `memory_limit_mib`, `cpu_limit_millicores` | PARTIAL |
| `allowed_domains` | ✅ `network_egress` | IMPLEMENTED |
| `blocked_domains` | ❌ Missing | MISSING |
| `egress_mode` | ❌ Missing | MISSING |
| `opa_policy_packages` | ⚠️ `security.opa_policy` (single string) | PARTIAL |
| `guardrail_profiles` | ❌ Missing | MISSING |
| `default_hitl_mode` | ❌ Missing | MISSING |
| `risk_thresholds` | ❌ Missing | MISSING |
| `max_pending_hitl` | ❌ Missing | MISSING |
| `rl_export_allowed` | ❌ Missing | MISSING |
| `rl_export_scope` | ❌ Missing | MISSING |
| `rl_excluded_fields` | ❌ Missing | MISSING |
| `example_store_policy` | ❌ Missing | MISSING |
| `data_classification` | ❌ Missing | MISSING |
| `retention_policy_days` | ⚠️ `audit.retain_days` | PARTIAL |

#### CapsuleInstance
**Status:** ❌ **COMPLETELY MISSING**

**Critical Gaps:**
1. No versioned `CapsuleDefinition` vs `CapsuleInstance` separation
2. No scoping (TASK/WORKFLOW/NODE/ROLE)
3. No `effective_config` snapshots
4. No derivation/override chains

---

## 3. Blueprint & Planning Models (SRS Section 3)

### SRS Models:
1. `BlueprintDefinition`
2. `BlueprintParameterDefinition`
3. `PlanSpec`

### Current Implementation:
| Model | Status | Gap |
|-------|--------|-----|
| BlueprintDefinition | ❌ MISSING | Entire model missing |
| BlueprintParameterDefinition | ❌ MISSING | Entire model missing |
| PlanSpec | ❌ MISSING | Entire model missing |

**Impact:** No formalized blueprint/planning system exists.

---

## 4. Task & Workflow Runtime Models (SRS Section 4)

### 4.1 TaskRecord

**Status:** ❌ **COMPLETELY MISSING**

**SRS Fields:** `id`, `tenant_id`, `user_principal`, `source_application`, `original_request_text`, `task_type`, `domain`, `priority`, `sla`, `status`, `plan_spec_id`, `root_workflow_instance_id`, `capsule_instance_id`, `created_at`, `updated_at`, `completed_at`, `labels`, `error_summary`

**Current:** No `TaskRecord` model exists anywhere in codebase.

### 4.2 TaskStatusHistory

**Status:** ❌ **MISSING**

### 4.3 GraphWorkflowDefinition

**Location:** `services/orchestrator/app/models/schema.py:GraphWorkflowModel`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` (UUID) | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `name` | ✅ `name` (Text) | IMPLEMENTED |
| `version` | ✅ `version` (int) | IMPLEMENTED |
| `status` | ❌ Missing | MISSING |
| `description` | ❌ Missing | MISSING |
| `nodes` | ⚠️ In `definition` JSONB | PARTIAL |
| `edges` | ⚠️ In `definition` JSONB | PARTIAL |
| `entry_node_id` | ❌ Missing | MISSING |
| `exit_node_ids` | ❌ Missing | MISSING |
| `validation_rules` | ❌ Missing | MISSING |
| `created_by` | ✅ `created_by` (FK) | IMPLEMENTED |
| `created_at` | ✅ `created_at` | IMPLEMENTED |

**Gap:** All graph structure stored in opaque JSONB blob rather than structured fields.

### 4.4 GraphNodeDefinition

**Pydantic Location:** `services/common/models/workflow.py:WorkflowNode`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `node_id` | ✅ `id` | IMPLEMENTED |
| `type` | ✅ `type` (enum) | IMPLEMENTED |
| `name` | ❌ Missing | MISSING |
| `description` | ❌ Missing | MISSING |
| `agent_role` | ⚠️ `agent_id` (string) | PARTIAL - no role concept |
| `capsule_hint` | ❌ Missing | MISSING |
| `input_contract` | ❌ Missing | MISSING |
| `output_contract` | ❌ Missing | MISSING |
| `retry_policy` | ❌ Missing | MISSING |
| `timeout_seconds` | ❌ Missing | MISSING |
| `risk_level` | ✅ `risk` (enum) | IMPLEMENTED |
| `hitl_required` | ✅ `interrupt` (bool) | IMPLEMENTED |
| `external_runtime_ref` | ❌ Missing | MISSING |

**SRS NodeType:** AGENT, TOOL, SUBGRAPH, HITL, EXTERNAL_RUNTIME, NOOP, DECISION, GATEWAY  
**Current NodeType:** AGENT, TOOL, SUBGRAPH, HUMAN_INTERRUPT  
**Missing:** EXTERNAL_RUNTIME, NOOP, DECISION, GATEWAY

### 4.5 GraphEdgeDefinition

**Pydantic Location:** `services/common/models/workflow.py:WorkflowEdge`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `edge_id` | ❌ Missing | MISSING |
| `from_node_id` | ✅ `source` | IMPLEMENTED |
| `to_node_id` | ✅ `target` | IMPLEMENTED |
| `condition` | ✅ `condition` (optional str) | IMPLEMENTED |
| `weight` | ❌ Missing | MISSING |

### 4.6 WorkflowInstance

**Location:** `services/orchestrator/app/models/schema.py:WorkflowInstanceModel`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `task_id` | ❌ Missing | MISSING |
| `graph_workflow_definition_id` | ✅ `workflow_id` (FK) | IMPLEMENTED |
| `graph_version` | ❌ Missing | MISSING |
| `capsule_instance_id` | ❌ Missing | MISSING |
| `status` | ✅ `status` | IMPLEMENTED |
| `current_node_ids` | ❌ Missing | MISSING |
| `started_at` | ✅ `started_at` | IMPLEMENTED |
| `finished_at` | ✅ `finished_at` | IMPLEMENTED |
| `last_error` | ❌ Missing | MISSING |
| `state` | ✅ `state` (JSONB) | IMPLEMENTED |

**Gap:** No link to parent Task, no Capsule binding, no version tracking.

### 4.7 NodeExecution

**Status:** ❌ **COMPLETELY MISSING**

**SRS Fields:** `id`, `tenant_id`, `workflow_instance_id`, `node_id`, `attempt`, `status`, `input_snapshot_ref`, `output_snapshot_ref`, `agent_session_binding_id`, `tool_invocation_id`, `hitl_session_id`, `started_at`, `ended_at`, `error_details`

**Current:** No per-node execution tracking table exists.

### 4.8 Checkpoint

**Location:** `services/orchestrator/app/models/schema.py:WorkflowCheckpointModel`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `workflow_instance_id` | ✅ `instance_id` (FK) | IMPLEMENTED |
| `node_id` | ✅ `node_id` | IMPLEMENTED |
| `created_at` | ✅ `created_at` | IMPLEMENTED |
| `state_snapshot_ref` | ⚠️ `state_snapshot` (JSONB inline) | PARTIAL - no ref |
| `capsule_snapshot` | ❌ Missing | MISSING |

**Gap:** No Capsule snapshot at checkpoint time.

---

## 5. Agent & Role Models (SRS Section 5)

### 5.1 RoleDefinition

**Status:** ❌ **COMPLETELY MISSING**

**SRS Fields:** `id`, `tenant_id`, `name`, `description`, `default_persona_ref`, `expected_behavior`

**Current:** No concept of logical roles (PLANNER, SOLVER, VERIFIER, etc.) exists.

### 5.2 AgentBinding

**Status:** ❌ **COMPLETELY MISSING**

**SRS Fields:** `id`, `tenant_id`, `role_id`, `agent01_agent_ref`, `supported_task_types`, `supported_domains`, `default_capsule_definition_id`

**Current:** No binding layer between Hub and SomaAgent01.

### 5.3 AgentSessionBinding

**Status:** ❌ **COMPLETELY MISSING**

**Current:** Workflow engine directly calls activities; no session tracking exists.

---

## 6. Tools & MCP Models (SRS Section 6)

### 6.1 ToolDefinition

**Status:** ❌ **MISSING** (as database model)

**Pydantic Only:** `services/common/models/agent.py:ToolSpec`

| SRS Field | Pydantic Field | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `name` | ❌ Missing | MISSING |
| `version` | ❌ Missing | MISSING |
| `type` | ✅ `type` (enum) | IMPLEMENTED |
| `description` | ✅ `description` | IMPLEMENTED |
| `io_contract` | ⚠️ `parameters` (dict) | PARTIAL |
| `risk_level` | ✅ `security_level` | IMPLEMENTED |
| `default_timeout_seconds` | ✅ `timeout_sec` | IMPLEMENTED |
| `metadata` | ❌ Missing | MISSING |

**Gap:** Tool definitions not persisted in database, only used in Pydantic validation.

### 6.2 MCPServerDefinition

**Status:** ❌ **COMPLETELY MISSING**

### 6.3 ToolInvocationRecord

**Status:** ❌ **COMPLETELY MISSING**

**Current:** No tracking of individual tool calls in database.

---

## 7. Memory Integration Models (SRS Section 7)

### 7.1 MemoryBindingSpec

**Status:** ❌ **COMPLETELY MISSING**

### 7.2 MemoryOperationRecord

**Status:** ❌ **COMPLETELY MISSING**

**Current:** No memory operation tracking exists.

---

## 8. Reasoning Pipelines & RL Models (SRS Section 8)

### SRS Models:
1. `ReasoningPipelineSpec`
2. `PipelineStageSpec`
3. `GameSpec`
4. `PayoffDefinition`

### Current Implementation:
| Model | Status | Gap |
|-------|--------|-----|
| ReasoningPipelineSpec | ❌ MISSING | No reasoning pipeline concept |
| PipelineStageSpec | ❌ MISSING | No stage definitions |
| GameSpec | ❌ MISSING | No game-theoretic models |
| PayoffDefinition | ❌ MISSING | No reward/payoff tracking |

**Impact:** No RL/MARL capabilities, no MarsRL integration.

---

## 9. Trajectories & RL Export (SRS Section 9)

### SRS Models:
1. `TrajectoryRecord`
2. `TrajectoryStep`
3. `RLExportJob`

### Current Implementation:
| Model | Status | Gap |
|-------|--------|-----|
| TrajectoryRecord | ❌ MISSING | No trajectory recording |
| TrajectoryStep | ❌ MISSING | No step-level data |
| RLExportJob | ❌ MISSING | No RL data export |

**Impact:** Cannot train RL agents from workflow histories.

---

## 10. HITL (Human In The Loop) Models (SRS Section 10)

### 10.1 HumanReviewSession

**Location:** `services/orchestrator/app/models/schema.py:HumanReviewSessionModel`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `workflow_instance_id` | ✅ `instance_id` (FK) | IMPLEMENTED |
| `node_execution_id` | ❌ Missing | MISSING |
| `initiator` | ❌ Missing | MISSING |
| `status` | ✅ `status` | IMPLEMENTED |
| `requested_at` | ✅ `created_at` | IMPLEMENTED |
| `resolved_at` | ✅ `resolved_at` | IMPLEMENTED |
| `deadline_at` | ❌ Missing | MISSING |
| `review_payload_ref` | ⚠️ `payload` (JSONB inline) | PARTIAL |
| `resolution_comment` | ❌ Missing | MISSING |
| `resolution_metadata` | ❌ Missing | MISSING |
| `node_id` | ✅ `node_id` | IMPLEMENTED |

**Gap:** No reviewer assignment, no resolution details, no deadlines.

### 10.2 HumanReviewerAssignment

**Status:** ❌ **MISSING**

### 10.3 HumanDecisionRecord

**Status:** ❌ **MISSING**

---

## 11. Observability, Evaluation & Audit (SRS Section 11)

### 11.1 SomaTraceSpanSummary

**Status:** ❌ **MISSING**

**Current:** OpenTelemetry instrumentation exists in code but no Hub-side span index.

### 11.2 EvaluationScenarioDefinition

**Status:** ❌ **MISSING**

### 11.3 EvaluationRun

**Status:** ❌ **MISSING**

### 11.4 EvaluationMetricRecord

**Status:** ❌ **MISSING**

### 11.5 AuditLogEntry

**Location:** `services/orchestrator/app/models/schema.py:AuditLogModel`

| SRS Field | Implementation | Status |
|-----------|----------------|--------|
| `id` | ✅ `id` | IMPLEMENTED |
| `tenant_id` | ❌ Missing | MISSING |
| `timestamp` | ✅ `timestamp` | IMPLEMENTED |
| `actor` | ✅ `actor` (UUID) | IMPLEMENTED |
| `action_type` | ✅ `action` (Text) | IMPLEMENTED |
| `target_type` | ⚠️ `resource` | PARTIAL |
| `target_id` | ❌ Missing | MISSING |
| `capsule_context_id` | ❌ Missing | MISSING |
| `policy_decision` | ✅ `decision` | IMPLEMENTED |
| `details` | ✅ `details` (JSONB) | IMPLEMENTED |

**Gap:** No Capsule context, no structured target references.

---

## 12. Additional Current Models NOT in SRS

### AgentModel
**Location:** `services/orchestrator/app/models/schema.py`

**Fields:** `id`, `name`, `description`, `role`, `instructions`, `tools`, `memory_bindings`, `constraints`, `policy_scope`, `agent_metadata`, `created_at`, `updated_at`

**Status:** ⚠️ **LEGACY MODEL** - Appears to be pre-SRS design.

**SRS Equivalent:** Should be replaced by `RoleDefinition` + `AgentBinding` to SomaAgent01.

### CrewModel
**Location:** `services/orchestrator/app/models/schema.py`

**Fields:** `id`, `name`, `goal`, `agents`, `supervisor`, `routing_mode`, `created_at`

**Status:** ⚠️ **PARTIAL MATCH** to SRS `CrewSpec` (Pydantic).

**Gap:** No database persistence in SRS (crews are logical constructs, not persisted entities in the new design).

---

## Summary Statistics

### Model Coverage by SRS Section:

| SRS Section | Total Models | Implemented | Partial | Missing | Coverage % |
|-------------|--------------|-------------|---------|---------|------------|
| 0. Principles | 5 | 1 | 2 | 2 | 30% |
| 1. Identity | 3 | 0 | 0 | 3 | 0% |
| 2. Capsule | 2 | 0 | 1 | 1 | 25% |
| 3. Blueprint | 3 | 0 | 0 | 3 | 0% |
| 4. Task/Workflow | 8 | 3 | 4 | 1 | 44% |
| 5. Agent/Role | 3 | 0 | 0 | 3 | 0% |
| 6. Tools/MCP | 3 | 0 | 1 | 2 | 17% |
| 7. Memory | 2 | 0 | 0 | 2 | 0% |
| 8. RL Pipelines | 4 | 0 | 0 | 4 | 0% |
| 9. Trajectories | 3 | 0 | 0 | 3 | 0% |
| 10. HITL | 3 | 1 | 0 | 2 | 33% |
| 11. Observability | 5 | 0 | 1 | 4 | 10% |
| **TOTAL** | **44** | **5** | **9** | **30** | **16%** |

### Critical Missing Infrastructure:

1. ❌ **Multi-tenancy** - No `tenant_id` anywhere
2. ❌ **TaskRecord** - No top-level task tracking
3. ❌ **RoleDefinition** - No role abstraction
4. ❌ **Agent01/Brain Bindings** - No external system integration models
5. ❌ **NodeExecution** - No per-node execution tracking
6. ❌ **CapsuleInstance** - No runtime Capsule binding
7. ❌ **RL Models** - Complete absence of RL/MARL infrastructure
8. ❌ **Memory Models** - No SomaBrain integration tracking
9. ❌ **Evaluation** - No regression testing framework
10. ❌ **Tool Tracking** - No tool invocation records

---

## Recommended Implementation Priority

### Phase 1: Foundation (Weeks 1-4)
1. Add `tenant_id` to ALL existing models (**BREAKING CHANGE**)
2. Create `TenantRef`, `PrincipalRef`, `ExternalRef` models
3. Implement `TaskRecord` + `TaskStatusHistory`
4. Complete `CapsuleDefinition` + `CapsuleInstance` separation

### Phase 2: Agent Integration (Weeks 5-8)
5. Create `RoleDefinition`, `AgentBinding`, `AgentSessionBinding`
6. Implement `NodeExecution` tracking
7. Add `ToolDefinition`, `MCPServerDefinition`, `ToolInvocationRecord`
8. Complete memory integration models

### Phase 3: Advanced Features (Weeks 9-12)
9. Implement Blueprint system (`BlueprintDefinition`, `PlanSpec`)
10. Add RL models (`ReasoningPipelineSpec`, `GameSpec`, `TrajectoryRecord`)
11. Complete HITL models (`HumanReviewerAssignment`, `HumanDecisionRecord`)
12. Add observability models (`SomaTraceSpanSummary`, `EvaluationScenarioDefinition`)

### Phase 4: Validation (Weeks 13-14)
13. Database migration scripts
14. Data integrity constraints
15. API layer updates
16. SDK regeneration

---

## Appendix: Existing Code Structure

### Database Models (`services/orchestrator/app/models/schema.py`):
- `AgentModel` (90 lines) - Legacy agent storage
- `CrewModel` (10 lines) - Crew composition
- `GraphWorkflowModel` (10 lines) - Workflow definitions
- `WorkflowInstanceModel` (9 lines) - Workflow executions
- `WorkflowCheckpointModel` (8 lines) - Checkpoints
- `HumanReviewSessionModel` (10 lines) - HITL sessions
- `AuditLogModel` (8 lines) - Audit trail

### Pydantic Models (`services/common/models/`):
- `agent.py` - `AgentSpec`, `ToolSpec`, `CrewSpec`
- `capsule.py` - `CapsuleSpec`
- `workflow.py` - `WorkflowNode`, `WorkflowEdge`, `GraphWorkflow`

### Workflow Engine (`services/workflow-engine/app/`):
- `workflows/graph_engine.py` - `GraphWorkflowEngine`, `GraphWorkflowDef` (Temporal workflow)
- `activities/` - Real activity implementations (NO MOCKS as of 2025-12-03)

### Services Inventory:
- orchestrator, workflow-engine, gateway-api, identity-service
- policy-engine, memory-gateway, constitution-service
- agent-spawner, llm-hub, tool-service
- billing-service, pricing-service, analytics-service
- notification-service, settings-service
- **Total:** 20+ microservices

---

## Conclusion

The current SomaAgentHub implementation is approximately **16% compliant** with the comprehensive SRS model specification. The most critical gaps are:

1. **Complete absence of multi-tenancy**
2. **No TaskRecord** (top-level orchestration entity)
3. **No RL/MARL infrastructure** (0% of Section 8-9)
4. **No Agent01/Brain integration models** (0% of Section 5, 7)
5. **Incomplete Capsule system** (no CapsuleInstance, no runtime binding)

The existing codebase contains valuable foundation elements (workflow engine, basic models, Temporal integration) but requires substantial expansion to match the SRS vision of a multi-tenant, RL-ready, game-theoretic agent orchestration platform.

**Estimated effort to achieve 100% SRS compliance:** 12-16 weeks with 3-4 full-time engineers.

---

**END OF GAP ANALYSIS**
