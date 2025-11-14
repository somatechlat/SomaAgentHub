"""Repository layer for capsule storage operations.

Provides a simple async repository around SQLModel for creating and
retrieving capsule records. The implementation intentionally keeps logic
minimal to satisfy the Sprint 1 test suite.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

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
            meta=metadata or {},
        )
        self.session.add(capsule)
        await self.session.flush()
        return capsule

    async def get_capsule(self, capsule_id: str, version: str) -> Optional[Capsule]:
        stmt = select(Capsule).where(
            (Capsule.capsule_id == capsule_id) & (Capsule.version == version)
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def list_capsules(self, capsule_id: str | None = None) -> List[Capsule]:
        stmt = select(Capsule)
        if capsule_id:
            stmt = stmt.where(Capsule.capsule_id == capsule_id)
        result = await self.session.exec(stmt)
        return result.all()
