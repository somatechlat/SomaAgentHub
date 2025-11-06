"""Tests for the Planner API endpoints.

The tests focus on the FastAPI layer, mocking out the underlying ``PlannerService``
and ``PlanRepository`` to avoid external LLM or database calls. ``httpx.AsyncClient``
is used with the FastAPI ``app`` instance to issue HTTP requests against the
router.
"""

from __future__ import annotations

import pytest
import httpx

# Import the FastAPI app for the orchestrator service.
from services.orchestrator.app.main import app

# Import the router module so we can monkey‑patch the singleton service/repo.
from services.orchestrator.app.api.planner import _service, _repo, router
from services.orchestrator.app.planner.schemas import ProjectPlan, PlannerRequest, PlannerContext


@pytest.fixture(autouse=True)
def include_router():
    """Ensure the planner router is mounted on the test app.

    The main ``app`` already includes the router via ``routes.py`` but the fixture
    guarantees it for isolated test runs.
    """
    app.include_router(router)
    yield


def dummy_plan(plan_id: str = "plan-1") -> ProjectPlan:
    """Create a minimal ``ProjectPlan`` instance for use in mocks."""
    return ProjectPlan(
        plan_id=plan_id,
        tenant="tenant-1",
        capsule="capsule-1",
        objective="demo objective",
        modules=[],
        tool_suggestions=[],
        risks=[],
        wizard_queue=[],
        metadata={},
    )


@pytest.mark.asyncio
async def test_generate_plan_success(monkeypatch):
    """POST /v1/planner/generate returns a persisted ProjectPlan."""
    expected = dummy_plan()

    async def fake_generate(request: PlannerRequest, context: PlannerContext) -> ProjectPlan:
        return expected

    monkeypatch.setattr(_service, "generate_plan", fake_generate)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "request": {
                "tenant": "tenant-1",
                "session_id": "sess-1",
                "user_prompt": "Create a web app",
                "persona": None,
                "metadata": {},
            },
            "context": {
                "capsule_candidates": [],
                "available_tools": [],
                "memory_snippets": [],
                "tenant_defaults": {},
            },
        }
        response = await client.post("/v1/planner/generate", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == expected.plan_id


@pytest.mark.asyncio
async def test_batch_generate_parallel(monkeypatch):
    """POST /v1/planner/batch/generate runs multiple generations concurrently."""
    plans = [dummy_plan(f"plan-{i}") for i in range(3)]

    async def fake_generate(request: PlannerRequest, context: PlannerContext) -> ProjectPlan:
        # Return the next plan from the list.
        return plans.pop(0)

    monkeypatch.setattr(_service, "generate_plan", fake_generate)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "requests": [
                {
                    "request": {
                        "tenant": "t",
                        "session_id": f"s{i}",
                        "user_prompt": f"prompt {i}",
                        "persona": None,
                        "metadata": {},
                    },
                    "context": {
                        "capsule_candidates": [],
                        "available_tools": [],
                        "memory_snippets": [],
                        "tenant_defaults": {},
                    },
                }
                for i in range(3)
            ]
        }
        response = await client.post("/v1/planner/batch/generate", json=payload)
        assert response.status_code == 201
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 3
        for plan in results:
            assert "plan_id" in plan


@pytest.mark.asyncio
async def test_refine_plan_success(monkeypatch):
    """POST /v1/planner/refine updates an existing plan."""
    stored = dummy_plan("stored-1")
    refined = dummy_plan("refined-1")

    class DummyRecord:
        def __init__(self, payload):
            self.payload = payload

    async def fake_get_plan(plan_id: str):
        return DummyRecord(payload=stored.dict())

    async def fake_refine(plan, updates, *, context=None):
        return refined

    monkeypatch.setattr(_repo, "get_plan", fake_get_plan)
    monkeypatch.setattr(_service, "refine_plan", fake_refine)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "plan_id": "stored-1",
            "updates": {"objective": "new objective"},
            "context": None,
        }
        response = await client.post("/v1/planner/refine", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == refined.plan_id


@pytest.mark.asyncio
async def test_get_and_delete_plan(monkeypatch):
    """GET and DELETE endpoints retrieve and remove a plan respectively."""
    stored = dummy_plan("stored-2")

    class DummyRecord:
        def __init__(self, payload):
            self.payload = payload

    async def fake_get_plan(plan_id: str):
        return DummyRecord(payload=stored.dict())

    async def fake_delete_plan(plan_id: str):
        return None

    monkeypatch.setattr(_repo, "get_plan", fake_get_plan)
    monkeypatch.setattr(_repo, "delete_plan", fake_delete_plan)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # GET
        get_resp = await client.get(f"/v1/planner/{stored.plan_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["plan_id"] == stored.plan_id

        # DELETE
        del_resp = await client.delete(f"/v1/planner/{stored.plan_id}")
        assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_list_plans(monkeypatch):
    """GET /v1/planner/list returns all stored plans."""
    stored = [dummy_plan(f"plan-{i}") for i in range(3)]

    class DummyRecord:
        def __init__(self, payload):
            self.payload = payload

    async def fake_list_plans():
        return [DummyRecord(payload=p.dict()) for p in stored]

    monkeypatch.setattr(_repo, "list_plans", fake_list_plans)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/v1/planner/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        returned_ids = {item["plan_id"] for item in data}
        expected_ids = {p.plan_id for p in stored}
        assert returned_ids == expected_ids


@pytest.mark.asyncio
async def test_batch_refine_parallel(monkeypatch):
    """POST /v1/planner/batch/refine processes multiple refinements concurrently."""
    # Prepare stored plans and the expected refined results.
    stored_plans = [dummy_plan(f"stored-{i}") for i in range(2)]
    refined_plans = [dummy_plan(f"refined-{i}") for i in range(2)]

    class DummyRecord:
        def __init__(self, payload):
            self.payload = payload

    async def fake_get_plan(plan_id: str):
        # Return the matching stored plan based on the id.
        for p in stored_plans:
            if p.plan_id == plan_id:
                return DummyRecord(payload=p.dict())
        return None

    async def fake_refine(plan, updates, *, context=None):
        # Map the incoming plan to the corresponding refined version.
        index = int(plan.plan_id.split("-")[-1])
        return refined_plans[index]

    monkeypatch.setattr(_repo, "get_plan", fake_get_plan)
    monkeypatch.setattr(_service, "refine_plan", fake_refine)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "requests": [
                {
                    "plan_id": f"stored-{i}",
                    "updates": {"objective": f"new objective {i}"},
                    "context": None,
                }
                for i in range(2)
            ]
        }
        response = await client.post("/v1/planner/batch/refine", json=payload)
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 2
        for i, plan in enumerate(results):
            assert plan["plan_id"] == refined_plans[i].plan_id