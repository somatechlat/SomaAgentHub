"""Repository abstraction for reading/writing project plans."""

from __future__ import annotations

from typing import List

from .models import PlanEvent, PlanModuleRecord, PlanRecord, ProvisioningTaskRecord, ToolBindingRecord


class PlanRepository:
    """Storage facade for plan lifecycle operations.

    The concrete persistence (Postgres, Memory Gateway, etc.) will be added during
    implementation. This interface allows API handlers and workflows to remain stable
    while backend details evolve.
    """

    async def create_plan(self, record: PlanRecord) -> None:
        raise NotImplementedError

    async def get_plan(self, plan_id: str) -> PlanRecord:
        raise NotImplementedError

    async def list_modules(self, plan_id: str) -> List[PlanModuleRecord]:
        raise NotImplementedError

    async def upsert_module(self, module: PlanModuleRecord) -> None:
        raise NotImplementedError

    async def append_event(self, event: PlanEvent) -> None:
        raise NotImplementedError

    async def list_events(self, plan_id: str) -> List[PlanEvent]:
        raise NotImplementedError

    async def upsert_tool_binding(self, binding: ToolBindingRecord) -> None:
        raise NotImplementedError

    async def list_tool_bindings(self, plan_id: str) -> List[ToolBindingRecord]:
        raise NotImplementedError

    async def upsert_provisioning_task(self, task: ProvisioningTaskRecord) -> None:
        raise NotImplementedError

    async def list_provisioning_tasks(self, plan_id: str) -> List[ProvisioningTaskRecord]:
        raise NotImplementedError

    async def delete_plan(self, plan_id: str) -> None:
        raise NotImplementedError
