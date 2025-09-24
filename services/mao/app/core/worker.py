"""Workflow execution worker for MAO."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_engine, get_session_maker, workflow_steps, workflows


class WorkflowExecutor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine = get_engine()
        self.session_maker = get_session_maker()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        while self._running:
            async with self.session_maker() as session:
                progressed = await self._process_once(session)
            if not progressed:
                await asyncio.sleep(self.settings.poll_interval_seconds)

    async def _process_once(self, session: AsyncSession) -> bool:
        result = await session.execute(
            select(workflow_steps, workflows.c.status)
            .join(workflows, workflows.c.id == workflow_steps.c.workflow_id)
            .where(workflow_steps.c.status == "pending")
            .order_by(workflow_steps.c.workflow_id, workflow_steps.c.step_index)
            .limit(1)
        )
        row = result.first()
        if not row:
            return False

        step = row[0]
        workflow_status = row[1]
        if workflow_status not in ("pending", "running"):
            return False

        await session.execute(
            update(workflows)
            .where(workflows.c.id == step.workflow_id)
            .values(status="running")
        )
        await session.execute(
            update(workflow_steps)
            .where(workflow_steps.c.id == step.id)
            .values(status="running")
        )
        await session.commit()

        result_text = await self._execute_step(step.workflow_id, step.step_index, step.persona, step.instruction)

        await session.execute(
            update(workflow_steps)
            .where(workflow_steps.c.id == step.id)
            .values(status="completed", result=result_text)
        )

        remaining = await session.scalar(
            select(workflow_steps.c.id)
            .where(workflow_steps.c.workflow_id == step.workflow_id, workflow_steps.c.status != "completed")
        )
        new_status = "completed" if remaining is None else "running"
        await session.execute(
            update(workflows)
            .where(workflows.c.id == step.workflow_id)
            .values(status=new_status)
        )
        await session.commit()
        return True

    async def _execute_step(self, workflow_id: int, step_index: int, persona: Optional[str], instruction: str) -> str:
        payload = {
            "workflow_id": workflow_id,
            "step_index": step_index,
            "persona": persona,
            "instruction": instruction,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.settings.orchestrator_url}/v1/sessions/start", json=payload)
        if resp.status_code >= 400:
            return f"error: {resp.text}"
        return resp.text or "ok"


executor = WorkflowExecutor()
