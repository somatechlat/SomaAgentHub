"""Asynchronous repository for ``BuildRun`` entities.

The original codebase only provided a synchronous ``SQLBuildRunRepository``
used by unit tests. Integration tests (``tests/orchestrator``) expect an
asynchronous interface with methods:

* ``create_build_run`` – insert a new ``BuildRun`` row.
* ``get_build_run`` – retrieve by ``build_id``.
* ``update_build_run_status`` – update status and optional metadata.
* ``get_build_runs_by_project`` – list all runs for a project.
* ``get_build_runs_by_status`` – list all runs with a given status.

We implement these methods using the existing ``BuildRun`` SQLModel defined in
``services.orchestrator.app.repository.models``. The repository works with an
``AsyncSession`` (SQLModel/SQLAlchemy async engine) to match the test fixtures.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BuildRun
from .interfaces import BuildRunRepository


class SQLBuildRunRepository(BuildRunRepository):
    """Async implementation of the ``BuildRunRepository`` protocol.

    The methods mirror the behaviour of the synchronous version but use the
    async ``AsyncSession`` API. ``create_build_run`` returns the persisted model
    with ``created_at`` populated by the database.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_build_run(
        self,
        build_id: str,
        project_id: str,
        workflow_type: str,
        status: str,
    ) -> BuildRun:
        br = BuildRun(
            id=uuid.UUID(build_id) if isinstance(build_id, str) else build_id,
            project_id=project_id,
            workflow_type=workflow_type,
            status=status,
            created_at=datetime.utcnow(),
        )
        self.session.add(br)
        await self.session.flush()
        return br

    async def get_build_run(self, build_id: str) -> Optional[BuildRun]:
        stmt = select(BuildRun).where(BuildRun.id == uuid.UUID(build_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_build_run_status(
        self,
        build_id: str,
        status: str,
        metadata: Optional[dict] = None,
    ) -> Optional[BuildRun]:
        from sqlalchemy import update

        stmt = (
            update(BuildRun)
            .where(BuildRun.id == uuid.UUID(build_id))
            .values(status=status, metadata=metadata)
            .returning(BuildRun)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.fetchone()

    async def get_build_runs_by_project(self, project_id: str) -> List[BuildRun]:
        stmt = select(BuildRun).where(BuildRun.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_build_runs_by_status(self, status: str) -> List[BuildRun]:
        stmt = select(BuildRun).where(BuildRun.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()
