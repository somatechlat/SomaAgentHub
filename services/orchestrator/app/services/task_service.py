"""
Task Service - Business logic for task orchestration

Handles task lifecycle, status transitions, and coordination with workflows.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.models.task import (
    TaskRecord,
    TaskRecordCreate,
    TaskRecordResponse,
    TaskRecordUpdate,
    TaskStatus,
    TaskStatusHistory,
    TaskStatusHistoryResponse,
)
from services.orchestrator.app.database import get_async_session


class TaskService:
    """Service for managing tasks and their lifecycle"""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session

    async def create_task(self, task_data: TaskRecordCreate) -> TaskRecordResponse:
        """
        Create a new task and record initial status.

        Args:
            task_data: Task creation data

        Returns:
            Created task
        """
        if self.session:
            return await self._create_task_impl(self.session, task_data)

        async with get_async_session() as session:
            return await self._create_task_impl(session, task_data)

    async def _create_task_impl(
        self, session: AsyncSession, task_data: TaskRecordCreate
    ) -> TaskRecordResponse:
        # Create task record
        task = TaskRecord(
            tenant_id=task_data.tenant_id,
            user_principal_id=task_data.user_principal_id,
            source_application=task_data.source_application,
            original_request_text=task_data.original_request_text,
            task_type=task_data.task_type,
            domain=task_data.domain,
            priority=task_data.priority,
            sla=task_data.sla,
            status=TaskStatus.RECEIVED,
            labels=task_data.labels,
        )

        session.add(task)
        await session.flush()  # Get task.id

        # Record initial status in history
        history = TaskStatusHistory(
            task_id=task.id,
            previous_status=None,
            new_status=TaskStatus.RECEIVED,
            actor_principal_id=task_data.user_principal_id,
        )

        session.add(history)
        await session.commit()
        await session.refresh(task)

        return TaskRecordResponse.from_orm(task)

    async def get_task(
        self, task_id: UUID, tenant_id: UUID
    ) -> TaskRecordResponse | None:
        """
        Get task by ID with tenant isolation.

        Args:
            task_id: Task UUID
            tenant_id: Tenant UUID (for isolation)

        Returns:
            Task if found and belongs to tenant, None otherwise
        """
        if self.session:
            return await self._get_task_impl(self.session, task_id, tenant_id)
        async with get_async_session() as session:
            return await self._get_task_impl(session, task_id, tenant_id)

    async def _get_task_impl(
        self, session: AsyncSession, task_id: UUID, tenant_id: UUID
    ) -> TaskRecordResponse | None:
        stmt = select(TaskRecord).where(
            and_(TaskRecord.id == task_id, TaskRecord.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            return TaskRecordResponse.from_orm(task)
        return None

    async def list_tasks(
        self,
        tenant_id: UUID,
        status: TaskStatus | None = None,
        task_type: str | None = None,
        user_principal_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskRecordResponse]:
        """
        List tasks with filters and tenant isolation.

        Args:
            tenant_id: Tenant UUID
            status: Optional status filter
            task_type: Optional task type filter
            user_principal_id: Optional user filter
            limit: Max results
            offset: Pagination offset

        Returns:
            List of tasks
        """
        if self.session:
            return await self._list_tasks_impl(
                self.session,
                tenant_id,
                status,
                task_type,
                user_principal_id,
                limit,
                offset,
            )
        async with get_async_session() as session:
            return await self._list_tasks_impl(
                session, tenant_id, status, task_type, user_principal_id, limit, offset
            )

    async def _list_tasks_impl(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        status: TaskStatus | None,
        task_type: str | None,
        user_principal_id: UUID | None,
        limit: int,
        offset: int,
    ) -> list[TaskRecordResponse]:
        stmt = select(TaskRecord).where(TaskRecord.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(TaskRecord.status == status)

        if task_type:
            stmt = stmt.where(TaskRecord.task_type == task_type)

        if user_principal_id:
            stmt = stmt.where(TaskRecord.user_principal_id == user_principal_id)

        stmt = stmt.order_by(TaskRecord.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await session.execute(stmt)
        tasks = result.scalars().all()

        return [TaskRecordResponse.from_orm(t) for t in tasks]

    async def update_task_status(
        self, task_id: UUID, tenant_id: UUID, update_data: TaskRecordUpdate
    ) -> TaskRecordResponse | None:
        """
        Update task status and record in history.

        Args:
            task_id: Task UUID
            tenant_id: Tenant UUID
            update_data: Status update data

        Returns:
            Updated task if found, None otherwise
        """
        if self.session:
            return await self._update_task_status_impl(
                self.session, task_id, tenant_id, update_data
            )
        async with get_async_session() as session:
            return await self._update_task_status_impl(
                session, task_id, tenant_id, update_data
            )

    async def _update_task_status_impl(
        self,
        session: AsyncSession,
        task_id: UUID,
        tenant_id: UUID,
        update_data: TaskRecordUpdate,
    ) -> TaskRecordResponse | None:
        stmt = select(TaskRecord).where(
            and_(TaskRecord.id == task_id, TaskRecord.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return None

        # Record status change in history
        history = TaskStatusHistory(
            task_id=task.id,
            previous_status=task.status,
            new_status=update_data.status,
            reason=update_data.reason,
            actor_principal_id=update_data.actor_principal_id,
        )

        # Update task
        task.status = update_data.status

        # Set completed_at if transitioning to terminal state
        if update_data.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            task.completed_at = datetime.utcnow()

        session.add(history)
        await session.commit()
        await session.refresh(task)

        return TaskRecordResponse.from_orm(task)

    async def get_task_history(
        self, task_id: UUID, tenant_id: UUID
    ) -> list[TaskStatusHistoryResponse]:
        """
        Get status history for a task.

        Args:
            task_id: Task UUID
            tenant_id: Tenant UUID

        Returns:
            List of status history entries
        """
        if self.session:
            return await self._get_task_history_impl(self.session, task_id, tenant_id)
        async with get_async_session() as session:
            return await self._get_task_history_impl(session, task_id, tenant_id)

    async def _get_task_history_impl(
        self, session: AsyncSession, task_id: UUID, tenant_id: UUID
    ) -> list[TaskStatusHistoryResponse]:
        # Verify task belongs to tenant
        task_stmt = select(TaskRecord).where(
            and_(TaskRecord.id == task_id, TaskRecord.tenant_id == tenant_id)
        )
        task_result = await session.execute(task_stmt)
        task = task_result.scalar_one_or_none()

        if not task:
            return []

        # Get history
        stmt = select(TaskStatusHistory).where(TaskStatusHistory.task_id == task_id)
        stmt = stmt.order_by(TaskStatusHistory.timestamp.asc())

        result = await session.execute(stmt)
        history = result.scalars().all()

        return [TaskStatusHistoryResponse.from_orm(h) for h in history]

    async def link_workflow_to_task(
        self, task_id: UUID, tenant_id: UUID, workflow_instance_id: UUID
    ) -> TaskRecordResponse | None:
        """
        Link a workflow instance to a task.

        Args:
            task_id: Task UUID
            tenant_id: Tenant UUID
            workflow_instance_id: Workflow instance UUID

        Returns:
            Updated task if found, None otherwise
        """
        if self.session:
            return await self._link_workflow_to_task_impl(
                self.session, task_id, tenant_id, workflow_instance_id
            )
        async with get_async_session() as session:
            return await self._link_workflow_to_task_impl(
                session, task_id, tenant_id, workflow_instance_id
            )

    async def _link_workflow_to_task_impl(
        self,
        session: AsyncSession,
        task_id: UUID,
        tenant_id: UUID,
        workflow_instance_id: UUID,
    ) -> TaskRecordResponse | None:
        stmt = select(TaskRecord).where(
            and_(TaskRecord.id == task_id, TaskRecord.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return None

        task.root_workflow_instance_id = workflow_instance_id

        await session.commit()
        await session.refresh(task)

        return TaskRecordResponse.from_orm(task)
