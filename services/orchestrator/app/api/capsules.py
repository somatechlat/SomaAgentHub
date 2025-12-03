"""FastAPI routes for capsule CRUD operations in the Orchestrator service.

Sprint 1 introduces a PostgreSQL‑backed capsule registry.  These endpoints
provide the same surface as the existing ``task‑capsule‑repo`` service but
operate on the Orchestrator's own database using the ``CapsuleRepository``
implemented in ``services.orchestrator.app.repository.capsule_repository``.
All handlers are async and use the shared ``get_session`` dependency from the
core ``database`` module.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..database import get_session
from ..models.capsule import CapsuleKind, CapsuleType, ExecutionMode
from ..repository.capsule_repository import CapsuleRepository

router = APIRouter(prefix="/v1/capsules", tags=["capsules"])


class CapsuleCreateRequest(BaseModel):
    capsule_id: str = Field(..., description="Human readable capsule identifier")
    version: str = Field(default="latest", description="Version tag")
    type: CapsuleType | None = None
    kind: CapsuleKind | None = None
    execution_mode: ExecutionMode | None = None
    required_roles: list[str] | None = None
    requires_payment: str = "false"
    http_config: dict | None = None
    manifest_yaml: str | None = None
    metadata: dict | None = None


class CapsuleResponse(BaseModel):
    id: str
    capsule_id: str
    version: str
    type: CapsuleType | None
    kind: CapsuleKind | None
    execution_mode: ExecutionMode | None
    required_roles: list[str]
    requires_payment: str
    http_config: dict
    manifest_yaml: str | None
    metadata: dict
    created_at: str
    updated_at: str


def get_repo(session=Depends(get_session)) -> CapsuleRepository:
    return CapsuleRepository(session)


@router.post("", response_model=CapsuleResponse, status_code=status.HTTP_201_CREATED)
async def create_capsule(req: CapsuleCreateRequest, repo: CapsuleRepository = Depends(get_repo)):
    capsule = await repo.create_capsule(
        capsule_id=req.capsule_id,
        version=req.version,
        type=req.type,
        kind=req.kind,
        execution_mode=req.execution_mode,
        required_roles=req.required_roles,
        requires_payment=req.requires_payment,
        http_config=req.http_config,
        manifest_yaml=req.manifest_yaml,
        metadata=req.metadata,
    )
    return CapsuleResponse(
        id=str(capsule.id),
        capsule_id=capsule.capsule_id,
        version=capsule.version,
        type=capsule.type,
        kind=capsule.kind,
        execution_mode=capsule.execution_mode,
        required_roles=capsule.required_roles,
        requires_payment=capsule.requires_payment,
        http_config=capsule.http_config,
        manifest_yaml=capsule.manifest_yaml,
        metadata=capsule.metadata_json,
        created_at=capsule.created_at.isoformat(),
        updated_at=capsule.updated_at.isoformat(),
    )


@router.get("", response_model=list[CapsuleResponse])
async def list_capsules(capsule_id: str | None = None, repo: CapsuleRepository = Depends(get_repo)):
    caps = await repo.list_capsules(capsule_id=capsule_id)
    return [
        CapsuleResponse(
            id=str(c.id),
            capsule_id=c.capsule_id,
            version=c.version,
            type=c.type,
            kind=c.kind,
            execution_mode=c.execution_mode,
            required_roles=c.required_roles,
            requires_payment=c.requires_payment,
            http_config=c.http_config,
            manifest_yaml=c.manifest_yaml,
            metadata=c.metadata_json,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in caps
    ]


@router.get("/{capsule_id}/{version}", response_model=CapsuleResponse)
async def get_capsule(capsule_id: str, version: str, repo: CapsuleRepository = Depends(get_repo)):
    capsule = await repo.get_capsule(capsule_id, version)
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")
    return CapsuleResponse(
        id=str(capsule.id),
        capsule_id=capsule.capsule_id,
        version=capsule.version,
        type=capsule.type,
        kind=capsule.kind,
        execution_mode=capsule.execution_mode,
        required_roles=capsule.required_roles,
        requires_payment=capsule.requires_payment,
        http_config=capsule.http_config,
        manifest_yaml=capsule.manifest_yaml,
        metadata=capsule.metadata_json,
        created_at=capsule.created_at.isoformat(),
        updated_at=capsule.updated_at.isoformat(),
    )


@router.delete("/{capsule_id}/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capsule(capsule_id: str, version: str, repo: CapsuleRepository = Depends(get_repo)):
    try:
        await repo.delete_capsule(capsule_id, version)
    except ValueError:
        raise HTTPException(status_code=404, detail="Capsule not found")
    return None
