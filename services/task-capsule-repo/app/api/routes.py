"""FastAPI routes for the Task Capsule Repository.

Provides CRUD operations for capsule definitions stored in PostgreSQL via
SQLModel. All routes are prefixed with ``/v1`` and are included in the main
application through ``app.api.__init__``.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..database import get_session
from ..models import Capsule, CapsuleType
from sqlalchemy import select

router = APIRouter(prefix="/v1", tags=["capsules"])


class CapsuleCreateRequest(BaseModel):
    capsule_id: str = Field(..., max_length=36, description="Human‑readable capsule identifier")
    version: str = Field(..., max_length=20)
    type: CapsuleType
    manifest_yaml: str
    metadata: Optional[dict] = Field(default_factory=dict)


class CapsuleResponse(BaseModel):
    id: str
    capsule_id: str
    version: str
    type: CapsuleType
    manifest_yaml: str
    metadata: dict
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, capsule: Capsule) -> "CapsuleResponse":
        return cls(
            id=str(capsule.id),
            capsule_id=capsule.capsule_id,
            version=capsule.version,
            type=capsule.type,
            manifest_yaml=capsule.manifest_yaml,
            metadata=capsule.metadata or {},
            created_at=capsule.created_at.isoformat(),
            updated_at=capsule.updated_at.isoformat(),
        )


@router.post("/capsules", response_model=CapsuleResponse, status_code=status.HTTP_201_CREATED)
async def create_capsule(
    payload: CapsuleCreateRequest,
    session=Depends(get_session),
):
    """Create a new capsule version.

    The combination of ``capsule_id`` and ``version`` must be unique.
    """
    # Ensure uniqueness
    stmt = select(Capsule).where(
        (Capsule.capsule_id == payload.capsule_id) & (Capsule.version == payload.version)
    )
    existing = await session.execute(stmt)
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Capsule version already exists",
        )

    capsule = Capsule(
        capsule_id=payload.capsule_id,
        version=payload.version,
        type=payload.type,
        manifest_yaml=payload.manifest_yaml,
        metadata=payload.metadata or {},
    )
    session.add(capsule)
    await session.flush()  # assign primary key
    return CapsuleResponse.from_orm(capsule)


@router.get("/capsules", response_model=List[CapsuleResponse])
async def list_capsules(
    capsule_id: Optional[str] = None,
    session=Depends(get_session),
):
    """List capsules, optionally filtered by ``capsule_id``."""
    stmt = select(Capsule)
    if capsule_id:
        stmt = stmt.where(Capsule.capsule_id == capsule_id)
    result = await session.execute(stmt)
    capsules = result.scalars().all()
    return [CapsuleResponse.from_orm(c) for c in capsules]


@router.get(
    "/capsules/{capsule_id}/{version}", response_model=CapsuleResponse
)
async def get_capsule(
    capsule_id: str,
    version: str,
    session=Depends(get_session),
):
    stmt = select(Capsule).where(
        (Capsule.capsule_id == capsule_id) & (Capsule.version == version)
    )
    result = await session.execute(stmt)
    capsule = result.scalars().first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    return CapsuleResponse.from_orm(capsule)


@router.put(
    "/capsules/{capsule_id}/{version}", response_model=CapsuleResponse
)
async def update_capsule(
    capsule_id: str,
    version: str,
    payload: CapsuleCreateRequest,
    session=Depends(get_session),
):
    stmt = select(Capsule).where(
        (Capsule.capsule_id == capsule_id) & (Capsule.version == version)
    )
    result = await session.execute(stmt)
    capsule = result.scalars().first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    # Update mutable fields
    capsule.type = payload.type
    capsule.manifest_yaml = payload.manifest_yaml
    capsule.metadata = payload.metadata or {}
    session.add(capsule)
    return CapsuleResponse.from_orm(capsule)


@router.delete(
    "/capsules/{capsule_id}/{version}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_capsule(
    capsule_id: str,
    version: str,
    session=Depends(get_session),
):
    stmt = select(Capsule).where(
        (Capsule.capsule_id == capsule_id) & (Capsule.version == version)
    )
    result = await session.execute(stmt)
    capsule = result.scalars().first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    session.delete(capsule)
    return None
