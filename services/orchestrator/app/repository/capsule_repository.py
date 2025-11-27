"""Repository layer for Capsule CRUD operations in the Orchestrator service.

The Sprint 1 roadmap requires a PostgreSQL‑backed capsule registry.  This
repository provides async helper methods that operate on a ``SQLModel``
``Session`` (the same pattern used by other repositories in the codebase).
All methods are fully typed and raise ``ValueError`` for missing records – the
calling API layer can translate those into appropriate HTTP responses.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.capsule import Capsule, CapsuleType, CapsuleKind, ExecutionMode


class CapsuleRepository:
    """Async repository for the ``Capsule`` model.

    The repository mirrors the interface of ``task_capsule_repo`` but operates
    on the Orchestrator's own database.  It is deliberately minimal – only the
    operations required by the Sprint 1 test suite are implemented.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_capsule(
        self,
        capsule_id: str,
        version: str = "latest",
        type: Optional[CapsuleType] = None,
        kind: Optional[CapsuleKind] = None,
        execution_mode: Optional[ExecutionMode] = None,
        required_roles: Optional[list[str]] = None,
        requires_payment: str = "false",
        http_config: Optional[dict] = None,
        manifest_yaml: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Capsule:
        capsule = Capsule(
            capsule_id=capsule_id,
            version=version,
            type=type,
            kind=kind,
            execution_mode=execution_mode,
            required_roles=required_roles or [],
            requires_payment=requires_payment,
            http_config=http_config or {},
            manifest_yaml=manifest_yaml,
            metadata_json=metadata or {},
        )
        self.session.add(capsule)
        await self.session.flush()
        return capsule

    async def get_capsule(self, capsule_id: str, version: str) -> Optional[Capsule]:
        stmt = select(Capsule).where(
            (Capsule.capsule_id == capsule_id) & (Capsule.version == version)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_capsules(self, capsule_id: Optional[str] = None) -> List[Capsule]:
        stmt = select(Capsule)
        if capsule_id:
            stmt = stmt.where(Capsule.capsule_id == capsule_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_capsule(self, capsule_id: str, version: str) -> None:
        capsule = await self.get_capsule(capsule_id, version)
        if capsule is None:
            raise ValueError("Capsule not found")
        await self.session.delete(capsule)
        await self.session.flush()
