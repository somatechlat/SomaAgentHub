"""Repository abstraction for reading/writing project plans."""

from __future__ import annotations

from sqlmodel import select

from ..database import get_async_session
from .models import (
    Plan,
    PlanModuleRecord,
    PlanEvent,
    ToolBindingRecord,
    ProvisioningTaskRecord,
)


class PlanRepository:
    """Storage facade for plan lifecycle operations.

    The concrete persistence (Postgres, Memory Gateway, etc.) will be added during
    implementation. This interface allows API handlers and workflows to remain stable
    while backend details evolve.
    """

    async def create_plan(self, record: dict) -> Plan:
        """Persist a new plan.

        ``record`` is a plain ``dict`` that matches the ``ProjectPlan`` schema.
        We store the full JSON payload in the ``payload`` column and also copy
        a few top‑level fields for indexing.
        """
        async with get_async_session() as session:
            plan = Plan(
                plan_id=record.get("plan_id"),
                tenant=record.get("tenant"),
                status=record.get("status", "draft"),
                payload=record,
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            return plan

    async def get_plan(self, plan_id: str) -> Plan | None:
        """Retrieve a plan by its *business* ``plan_id``.

        The ``Plan`` model uses an auto‑generated UUID primary key ``id`` while
        the external API works with the ``plan_id`` column. The original
        implementation mistakenly used ``session.get`` which looks up the primary
        key, causing ``GET /v1/planner/<plan_id>`` to fail when ``plan_id`` is a
        string (e.g., ``"list"``) and resulting in a ``StatementError``. We now
        query the ``plan_id`` column explicitly.
        """
        async with get_async_session() as session:
            statement = select(Plan).where(Plan.plan_id == plan_id)
            result = await session.exec(statement)
            return result.first()

    async def list_modules(self, plan_id: str) -> list[PlanModuleRecord]:
        raise NotImplementedError

    async def upsert_module(self, module: PlanModuleRecord) -> None:
        raise NotImplementedError

    async def append_event(self, event: PlanEvent) -> None:
        raise NotImplementedError

    async def list_events(self, plan_id: str) -> list[PlanEvent]:
        raise NotImplementedError

    async def upsert_tool_binding(self, binding: ToolBindingRecord) -> None:
        raise NotImplementedError

    async def list_tool_bindings(self, plan_id: str) -> list[ToolBindingRecord]:
        raise NotImplementedError

    async def upsert_provisioning_task(self, task: ProvisioningTaskRecord) -> None:
        raise NotImplementedError

    async def list_provisioning_tasks(
        self, plan_id: str
    ) -> list[ProvisioningTaskRecord]:
        raise NotImplementedError

    async def delete_plan(self, plan_id: str) -> None:
        async with get_async_session() as session:
            plan = await session.get(Plan, plan_id)
            if plan:
                await session.delete(plan)
                await session.commit()

    async def list_plans(self) -> list[Plan]:
        """Return all stored plans.

        This lightweight helper is used by the public ``/v1/planner/list``
        endpoint to provide a simple overview of existing plans. It returns the
        full ``Plan`` ORM objects, which callers can then project to the needed
        fields (e.g., ``plan_id``, ``tenant``, ``status``).
        """
        async with get_async_session() as session:
            result = await session.exec(select(Plan))
            return result.all()
