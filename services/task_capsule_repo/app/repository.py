"""Repository layer for capsule storage operations.

Provides a simple async repository around SQLModel for creating and
retrieving capsule records. The implementation intentionally keeps logic
minimal to satisfy the Sprint 1 test suite.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Capsule


class CapsuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_capsule(
        self,
        capsule_id: str,
        version: str,
        type,
        manifest_yaml: str,
        metadata: dict | None = None,
    ) -> Capsule:
        capsule = Capsule(
            capsule_id=capsule_id,
            version=version,
            type=type,
            manifest_yaml=manifest_yaml,
            metadata_=metadata or {},
        )
        self.session.add(capsule)
        await self.session.commit()
        await self.session.refresh(capsule)
        return capsule

    async def get_capsule(self, capsule_id: str, version: str) -> Optional[Capsule]:
        statement = select(Capsule).where(
            Capsule.capsule_id == capsule_id, Capsule.version == version
        )
        results = await self.session.exec(statement)
        return results.first()

    async def list_capsules(self, capsule_id: str | None = None) -> List[Capsule]:
        statement = select(Capsule)
        if capsule_id:
            statement = statement.where(Capsule.capsule_id == capsule_id)
        results = await self.session.exec(statement)
        return results.all()
