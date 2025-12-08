from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlmodel import JSON, Column, Field, SQLModel

from services.common.models.capsule import CapsuleSpec

from ..database import get_session

router = APIRouter(tags=["capsules"])


# DB Model for Capsules (SQLModel)
class CapsuleModel(SQLModel, table=True):
    __tablename__ = "capsules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    version: str
    content: dict = Field(default={}, sa_column=Column(JSON))
    created_at: str


@router.post(
    "/capsules", response_model=CapsuleSpec, status_code=status.HTTP_201_CREATED
)
async def create_capsule(
    capsule: CapsuleSpec, session: AsyncSession = Depends(get_session)
):
    """Register a new capsule."""
    # Check if name/version exists
    name = capsule.metadata.get("name")
    version = capsule.metadata.get("version")

    if not name or not version:
        raise HTTPException(
            status_code=400, detail="Capsule metadata must contain name and version"
        )

    stmt = select(CapsuleModel).where(
        CapsuleModel.name == name, CapsuleModel.version == version
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Capsule {name}:{version} already exists"
        )

    db_capsule = CapsuleModel(
        name=name,
        version=version,
        content=capsule.dict(by_alias=True),
        created_at=capsule.metadata.get("createdAt", ""),
    )
    session.add(db_capsule)
    await session.commit()
    await session.refresh(db_capsule)
    return capsule


@router.get("/capsules/{name}/{version}", response_model=CapsuleSpec)
async def get_capsule(
    name: str, version: str, session: AsyncSession = Depends(get_session)
):
    """Get capsule by name and version."""
    stmt = select(CapsuleModel).where(
        CapsuleModel.name == name, CapsuleModel.version == version
    )
    result = await session.execute(stmt)
    db_capsule = result.scalar_one_or_none()
    if not db_capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    return CapsuleSpec(**db_capsule.content)
