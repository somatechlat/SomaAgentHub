"""Repository abstraction for reading/writing project plans."""

from __future__ import annotations

from sqlmodel import select

from ..database import get_async_session
from .models import (
from services.common.config.base_settings import resolve_env
    Plan,
    PlanEvent,
    PlanModuleRecord,
    ProvisioningTaskRecord,
    ToolBindingRecord,
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
        plan = await self.get_plan(plan_id)
        if not plan:
            return []
        modules = (plan.payload or {}).get("modules", [])
        records: list[PlanModuleRecord] = []
        for m in modules:
            records.append(
                PlanModuleRecord(
                    plan_id=plan_id,
                    module_id=m.get("module_id") or m.get("id") or "",
                    status=m.get("status", "draft"),
                    dependencies=list(m.get("dependencies", [])),
                    answers=dict(m.get("answers", {})),
                )
            )
        return records

    async def upsert_module(self, module: PlanModuleRecord) -> None:
        async with get_async_session() as session:
            stmt = select(Plan).where(Plan.plan_id == module.plan_id)
            result = await session.exec(stmt)
            plan = result.first()
            if not plan:
                return
            payload = dict(plan.payload or {})
            modules = list(payload.get("modules", []))
            updated = False
            for idx, m in enumerate(modules):
                mid = m.get("module_id") or m.get("id")
                if mid == module.module_id:
                    modules[idx] = {
                        **m,
                        "module_id": module.module_id,
                        "status": module.status,
                        "dependencies": module.dependencies,
                        "answers": module.answers,
                    }
                    updated = True
                    break
            if not updated:
                modules.append(
                    {
                        "module_id": module.module_id,
                        "status": module.status,
                        "dependencies": module.dependencies,
                        "answers": module.answers,
                    }
                )
            payload["modules"] = modules
            plan.payload = payload
            await session.commit()
            await session.refresh(plan)

    async def append_event(self, event: PlanEvent) -> None:
        async with get_async_session() as session:
            stmt = select(Plan).where(Plan.plan_id == event.plan_id)
            result = await session.exec(stmt)
            plan = result.first()
            if not plan:
                return
            payload = dict(plan.payload or {})
            events = list(payload.get("events", []))
            events.append(
                {
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                }
            )
            payload["events"] = events
            plan.payload = payload
            await session.commit()
            await session.refresh(plan)

    async def list_events(self, plan_id: str) -> list[PlanEvent]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return []
        events_raw = (plan.payload or {}).get("events", [])
        out: list[PlanEvent] = []
        for e in events_raw:
            out.append(
                PlanEvent(
                    plan_id=plan_id,
                    event_type=e.get("event_type", "unknown"),
                    payload=e.get("payload") or {},
                )
            )
        return out

    async def upsert_tool_binding(self, binding: ToolBindingRecord) -> None:
        async with get_async_session() as session:
            stmt = select(Plan).where(Plan.plan_id == binding.plan_id)
            result = await session.exec(stmt)
            plan = result.first()
            if not plan:
                return
            payload = dict(plan.payload or {})
            bindings = list(payload.get("tool_bindings", []))
            updated = False
            for i, tb in enumerate(bindings):
                if tb.get("capability") == binding.capability:
                    bindings[i] = {
                        **tb,
                        "capability": binding.capability,
                        "tool_name": binding.tool_name,
                        "status": binding.status,
                        "metadata": binding.metadata,
                    }
                    updated = True
                    break
            if not updated:
                bindings.append(
                    {
                        "capability": binding.capability,
                        "tool_name": binding.tool_name,
                        "status": binding.status,
                        "metadata": binding.metadata,
                    }
                )
            payload["tool_bindings"] = bindings
            plan.payload = payload
            await session.commit()
            await session.refresh(plan)

    async def list_tool_bindings(self, plan_id: str) -> list[ToolBindingRecord]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return []
        raw = (plan.payload or {}).get("tool_bindings", [])
        out: list[ToolBindingRecord] = []
        for tb in raw:
            out.append(
                ToolBindingRecord(
                    plan_id=plan_id,
                    capability=tb.get("capability", ""),
                    tool_name=tb.get("tool_name", ""),
                    status=tb.get("status", "unknown"),
                    metadata=tb.get("metadata") or {},
                )
            )
        return out

    async def upsert_provisioning_task(self, task: ProvisioningTaskRecord) -> None:
        async with get_async_session() as session:
            stmt = select(Plan).where(Plan.plan_id == task.plan_id)
            result = await session.exec(stmt)
            plan = result.first()
            if not plan:
                return
            payload = dict(plan.payload or {})
            tasks = list(payload.get("provisioning_tasks", []))
            updated = False
            for i, t in enumerate(tasks):
                if t.get("task_id") == task.task_id:
                    tasks[i] = {
                        **t,
                        "task_id": task.task_id,
                        "capsule_id": task.capsule_id,
                        "status": task.status,
                        "metadata": task.metadata,
                        "last_updated_at": task.last_updated_at.isoformat(),
                    }
                    updated = True
                    break
            if not updated:
                tasks.append(
                    {
                        "task_id": task.task_id,
                        "capsule_id": task.capsule_id,
                        "status": task.status,
                        "metadata": task.metadata,
                        "last_updated_at": task.last_updated_at.isoformat(),
                    }
                )
            payload["provisioning_tasks"] = tasks
            plan.payload = payload
            await session.commit()
            await session.refresh(plan)

    async def list_provisioning_tasks(
        self, plan_id: str
    ) -> list[ProvisioningTaskRecord]:
        plan = await self.get_plan(plan_id)
        if not plan:
            return []
        raw = (plan.payload or {}).get("provisioning_tasks", [])
        out: list[ProvisioningTaskRecord] = []
        for t in raw:
            out.append(
                ProvisioningTaskRecord(
                    plan_id=plan_id,
                    task_id=t.get("task_id", ""),
                    capsule_id=t.get("capsule_id", ""),
                    status=t.get("status", "unknown"),
                    metadata=t.get("metadata") or {},
                )
            )
        return out

    async def delete_plan(self, plan_id: str) -> None:
        async with get_async_session() as session:
            statement = select(Plan).where(Plan.plan_id == plan_id)
            result = await session.exec(statement)
            plan = result.first()
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
