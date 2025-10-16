# TEST REFACTORING ROADMAP

**Status**: Tests use fake clients and don't test real functionality  
**Approach**: Keep tests temporarily, but document what needs to be real

---

## Current Test Structure (Using Fakes)

### ❌ Orchestrator Tests (Using FakeTemporalClient)
**File**: `services/orchestrator/tests/conftest.py`  
**Problem**: Monkeypatches Temporal client, tests never fail  

**Tests affected**:
- `test_session_start_initiates_temporal_workflow` 
- `test_session_status_returns_workflow_result`
- `test_mao_start_initiates_workflow`
- `test_mao_status_returns_result`

### ❌ LangGraph Tests (Using DummyStateGraph)
**File**: `services/orchestrator/tests/integrations/test_langgraph_adapter.py`  
**Problem**: Monkeypatches LangGraph, tests never run real graphs  

**Tests affected**:
- `test_langgraph_routing_basic`
- `test_langgraph_routing_requires_nodes`
- `test_langgraph_routing_edge_validation`

### ❌ AutoGen Tests (Using DummyAssistantAgent, etc.)
**File**: `services/orchestrator/tests/integrations/test_autogen_adapter.py`  
**Problem**: Complete mocks, never tests real multi-agent collaboration

### ❌ CrewAI Tests (Using DummyAgent, etc.)
**File**: `services/orchestrator/tests/integrations/test_crewai_adapter.py`  
**Problem**: Complete mocks, never tests real crew coordination

---

## Refactoring Strategy

### Phase 1: Mark as Integration Tests (NOT Unit Tests)
Move these to `tests/integration/` and mark as requiring real dependencies:

```python
# tests/integration/test_orchestrator_workflows.py
import pytest

pytestmark = pytest.mark.integration  # Requires real Temporal, LangGraph, etc.

def test_session_workflow_with_real_temporal():
    """Test against REAL Temporal server (from docker-compose)."""
    # No monkeypatching - use real Temporal client
    # Can timeout, fail, retry - tests real behavior
```

### Phase 2: Keep Unit Tests Simple
Create simple unit tests that DON'T test workflow execution:

```python
# tests/unit/test_orchestrator_routes.py
def test_session_start_route_validates_input():
    """Test route validation (no workflow execution)."""
    client = TestClient(app)
    # Invalid payload
    response = client.post("/v1/sessions/start", json={})
    assert response.status_code == 400  # Bad request

def test_session_start_route_returns_202():
    """Test route returns correct status."""
    client = TestClient(app)
    # Valid payload
    response = client.post("/v1/sessions/start", json={...})
    assert response.status_code == 202  # Accepted
    assert "workflow_id" in response.json()
```

### Phase 3: Real Integration Tests
Create tests that use REAL services from docker-compose:

```python
# tests/integration/test_temporal_integration.py
@pytest.mark.integration
async def test_real_temporal_workflow_execution():
    """Test REAL workflow against actual Temporal server."""
    # Connect to Temporal server running in docker-compose
    client = await Client.connect("localhost:7233")
    
    # Start REAL workflow
    handle = await client.execute_workflow(
        "multi-agent-orchestration-workflow",
        payload,
        id="test-workflow-001",
        task_queue="soma-tasks",
    )
    
    # Wait for completion
    result = await handle.result(timeout=30)
    
    # Test REAL behavior:
    assert result.status == "completed"
    assert len(result.agent_results) == len(payload.directives)
    assert all(r.slm_response for r in result.agent_results)
```

---

## Recommended Timeline

| Phase | Week | Task |
|-------|------|------|
| 1 | Week 1 | Mark test fakes as "integration-only" with comments |
| 2 | Week 1 | Create unit tests that DON'T use fakes |
| 3 | Week 2-3 | Write real integration tests using docker-compose services |
| 4 | Week 3-4 | Remove fake implementations entirely |

---

## What's Left To Do

### Immediate (Week 1)
1. [ ] Add `# FIXME: Replace with real Temporal tests` comments to test_routes.py
2. [ ] Add `# FIXME: Replace with real LangGraph tests` comments to test_langgraph_adapter.py
3. [ ] Add `# FIXME: Replace with real AutoGen tests` comments to test_autogen_adapter.py
4. [ ] Add `# FIXME: Replace with real Crew tests` comments to test_crewai_adapter.py

### Soon (Week 2)
5. [ ] Create `tests/integration/conftest.py` with REAL Temporal connection
6. [ ] Create `tests/integration/test_orchestrator_workflows.py` with real tests
7. [ ] Create `tests/integration/test_langgraph_workflows.py` with real LangGraph tests

### Later (Week 3-4)
8. [ ] Delete or archive old fake test implementations
9. [ ] Update CI/CD to run integration tests separately
10. [ ] Document test execution requirements in README

---

## Current Status

### Production Code Fixes: ✅ COMPLETE
- Replaced dummy RAG fallback with real error handling
- Replaced fake job execution with real task dispatcher
- Replaced placeholder cost estimation with real rates
- Added real health checks
- Added real migration validation

### Test Refactoring: ⏳ IN PROGRESS
- Marked issues in MOCKS_AND_FAKES_AUDIT.md
- Created this roadmap
- Next: Add comments to tests + create real integration tests

### Timeline to True Reality: 3-4 weeks
