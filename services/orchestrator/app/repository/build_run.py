        synchronous repository for ``BuildRun`` entities.

        original codebase only provided a synchronous ``SQLBuildRunRepository``
         by unit tests. Integration tests (``tests/orchestrator``) expect an
         chronous interface with methods:

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
                emit_event: bool = False,
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
                    if emit_event:
                        eate an orchestration.started outbox event
                        from .outbox import OutboxEvent

                        event = OutboxEvent(
                        event_type="orchestration.started",
                        aggregate_id=str(br.id),
                        event_data={
                        "mao_id": str(br.id),
                        "project_id": project_id,
                        "workflow_type": workflow_type,
                        },
                        created_at=datetime.utcnow(),
                        )
                        self.session.add(event)
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
            emit_event: bool = False,
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
                updated_br = result.fetchone()
                if emit_event and updated_br:
                    from .outbox import OutboxEvent

                    event = OutboxEvent(
                    event_type="orchestration.completed",
                    aggregate_id=str(build_id),
                    event_data={
                    "status": status,
                    "duration": metadata.get("duration") if metadata else None,
                    },
                    created_at=datetime.utcnow(),
                    )
                    self.session.add(event)
                    await self.session.flush()
                    return updated_br

                    async def get_build_runs_by_project(self, project_id: str, limit: int | None = None, offset: int = 0) -> List[BuildRun]:
            stmt = select(BuildRun).where(BuildRun.project_id == project_id).offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)
                result = await self.session.execute(stmt)
                return result.scalars().all()

                async def get_build_runs_by_status(self, status: str) -> List[BuildRun]:
                    stmt = select(BuildRun).where(BuildRun.status == status)
                    result = await self.session.execute(stmt)
                    return result.scalars().all()
