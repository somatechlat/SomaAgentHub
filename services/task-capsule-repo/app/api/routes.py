"""API endpoints for task capsule marketplace."""

from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import (
    capsule_installations,
    capsule_packages,
    capsule_reviews,
    get_session,
    list_approved_packages,
)
from ..core.loader import get_loader
from .schemas import (
    CapsuleCatalogEntry,
    CapsuleDetail,
    CapsuleInstallRequest,
    CapsuleInstallResponse,
    CapsuleInstallationListResponse,
    CapsuleReviewRequest,
    CapsuleReviewResponse,
    CapsuleRollbackRequest,
    CapsuleSubmissionListResponse,
    CapsuleSubmissionRequest,
    CapsuleSubmissionResponse,
    CapsuleSummary,
)

router = APIRouter(prefix="/v1", tags=["capsules"])


async def _resolve_package_row(
    session: AsyncSession,
    capsule_id: str,
    version: str | None,
):
    stmt = (
        select(capsule_packages)
        .where(
            capsule_packages.c.capsule_id == capsule_id,
            capsule_packages.c.status == "approved",
        )
        .order_by(capsule_packages.c.created_at.desc(), capsule_packages.c.id.desc())
    )
    if version:
        stmt = stmt.where(capsule_packages.c.version == version)
    result = await session.execute(stmt)
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved capsule version not found")
    return row


def _installation_row_to_response(row) -> CapsuleInstallResponse:
    return CapsuleInstallResponse(
        installation_id=row["installation_id"],
        package_id=row["package_id"],
        capsule_id=row["capsule_id"],
        version=row["version"],
        tenant_id=row["tenant_id"],
        environment=row["environment"],
        status=row["status"],
        installed_at=row["installed_at"],
        installed_by=row["installed_by"],
        notes=row.get("notes"),
    )


def _installation_select():
    return (
        select(
            capsule_installations.c.id.label("installation_id"),
            capsule_installations.c.package_id,
            capsule_installations.c.tenant_id,
            capsule_installations.c.environment,
            capsule_installations.c.status,
            capsule_installations.c.installed_at,
            capsule_installations.c.installed_by,
            capsule_installations.c.notes,
            capsule_packages.c.capsule_id,
            capsule_packages.c.version,
        )
        .select_from(
            capsule_installations.join(
                capsule_packages,
                capsule_installations.c.package_id == capsule_packages.c.id,
            )
        )
    )


async def _fetch_installation(session: AsyncSession, installation_id: int):
    stmt = _installation_select().where(capsule_installations.c.id == installation_id)
    result = await session.execute(stmt)
    return result.mappings().first()


@router.get("/capsules")
async def list_capsules(
    session: AsyncSession = Depends(get_session),
) -> dict[str, list[CapsuleCatalogEntry]]:
    """Return full capsule catalog (filesystem + approved marketplace packages)."""

    loader = get_loader()
    static_capsules = loader.load_all()
    static_entries = [
        CapsuleCatalogEntry(
            id=capsule.get("id"),
            version=capsule.get("version", "unknown"),
            summary=capsule.get("summary"),
            type=capsule.get("type", "capsule"),
            source="filesystem",
        )
        for capsule in static_capsules
    ]

    marketplace_rows = await list_approved_packages(session)
    marketplace_entries = [
        CapsuleCatalogEntry(
            id=row["capsule_id"],
            version=row["version"],
            summary=row.get("summary"),
            type="capsule",
            source="marketplace",
        )
        for row in marketplace_rows
    ]

    combined = static_entries + marketplace_entries
    return {"capsules": combined}


@router.get("/", include_in_schema=False)
async def list_capsules_root(
    session: AsyncSession = Depends(get_session),
) -> dict[str, list[CapsuleCatalogEntry]]:
    """Compatibility shim for earlier clients requesting `/v1/`."""

    return await list_capsules(session=session)


@router.get("/capsules/{capsule_id}", response_model=CapsuleDetail)
async def read_capsule(
    capsule_id: str,
    version: str | None = Query(default=None, description="Optional version filter"),
    session: AsyncSession = Depends(get_session),
) -> CapsuleDetail:
    """Return capsule detail including status (filesystem or marketplace)."""

    loader = get_loader()
    capsule = loader.load_one(capsule_id)
    if capsule is not None:
        return CapsuleDetail(capsule=capsule, status="filesystem", submission_id=None)

    stmt = select(capsule_packages).where(capsule_packages.c.capsule_id == capsule_id)
    if version:
        stmt = stmt.where(capsule_packages.c.version == version)
    stmt = stmt.order_by(capsule_packages.c.id.desc())

    result = await session.execute(stmt)
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capsule not found")

    definition = json.loads(row["definition"])
    compliance = (
        json.loads(row["compliance_report"])
        if row.get("compliance_report")
        else None
    )
    return CapsuleDetail(
        capsule=definition,
        status=row["status"],
        submission_id=row["id"],
        compliance_report=compliance,
    )


@router.post(
    "/submissions",
    response_model=CapsuleSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_capsule(
    request: CapsuleSubmissionRequest,
    session: AsyncSession = Depends(get_session),
) -> CapsuleSubmissionResponse:
    """Submit capsule manifest for marketplace review."""

    canonical = json.dumps(request.definition, sort_keys=True, separators=(",", ":"))
    computed_hash = sha256(canonical.encode("utf-8")).hexdigest()
    if computed_hash != request.attestation_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attestation hash mismatch")

    compliance_blob = (
        json.dumps(request.compliance_report, sort_keys=True)
        if request.compliance_report is not None
        else None
    )

    insert_stmt = (
        insert(capsule_packages)
        .values(
            capsule_id=request.capsule_id,
            version=request.version,
            owner=request.owner,
            summary=request.summary,
            attestation_hash=computed_hash,
            attestation_signature=request.attestation_signature,
            definition=canonical,
            compliance_report=compliance_blob,
            tenant_scope=request.tenant_scope,
        )
        .returning(capsule_packages)
    )

    try:
        result = await session.execute(insert_stmt)
        await session.commit()
    except IntegrityError as exc:  # user submitted existing version
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Capsule version already submitted") from exc

    row = result.mappings().one()
    return CapsuleSubmissionResponse(
        id=row["id"],
        capsule_id=row["capsule_id"],
        version=row["version"],
        status=row["status"],
        attestation_hash=row["attestation_hash"],
        reviewer=row.get("reviewer"),
    )


@router.get("/submissions", response_model=CapsuleSubmissionListResponse)
async def list_submissions(
    status_filter: str | None = Query(default=None, description="Filter by status"),
    session: AsyncSession = Depends(get_session),
) -> CapsuleSubmissionListResponse:
    """List capsule submissions with optional status filter."""

    stmt = select(capsule_packages)
    if status_filter:
        stmt = stmt.where(capsule_packages.c.status == status_filter)
    stmt = stmt.order_by(capsule_packages.c.created_at.desc())

    result = await session.execute(stmt)
    summaries = [CapsuleSummary.model_validate(row) for row in result.mappings().all()]
    return CapsuleSubmissionListResponse(submissions=summaries)


@router.post(
    "/submissions/{submission_id}/review",
    response_model=CapsuleReviewResponse,
)
async def review_submission(
    submission_id: int,
    request: CapsuleReviewRequest,
    session: AsyncSession = Depends(get_session),
) -> CapsuleReviewResponse:
    """Approve or reject a capsule submission."""

    fetch_stmt = select(capsule_packages).where(capsule_packages.c.id == submission_id)
    result = await session.execute(fetch_stmt)
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    decision_status = "approved" if request.decision == "approve" else "rejected"
    now = datetime.utcnow()
    update_values = {
        "status": decision_status,
        "reviewer": request.reviewer,
        "updated_at": now,
    }
    if decision_status == "approved":
        update_values["approved_at"] = now
        update_values["rejected_reason"] = None
    else:
        update_values["approved_at"] = None
        update_values["rejected_reason"] = request.notes or ""

    update_stmt = (
        update(capsule_packages)
        .where(capsule_packages.c.id == submission_id)
        .values(update_values)
        .returning(capsule_packages)
    )
    await session.execute(update_stmt)

    review_stmt = insert(capsule_reviews).values(
        package_id=submission_id,
        reviewer=request.reviewer,
        decision=decision_status,
        notes=request.notes,
        is_override=request.is_override,
    )
    await session.execute(review_stmt)
    await session.commit()

    refreshed = await session.execute(fetch_stmt)
    refreshed_row = refreshed.mappings().first()

    return CapsuleReviewResponse(
        id=submission_id,
        status=refreshed_row["status"],
        reviewer=refreshed_row.get("reviewer"),
        approved_at=refreshed_row.get("approved_at"),
        rejected_reason=refreshed_row.get("rejected_reason"),
    )


@router.post(
    "/installations",
    response_model=CapsuleInstallResponse,
    status_code=status.HTTP_201_CREATED,
)
async def install_capsule(
    payload: CapsuleInstallRequest,
    session: AsyncSession = Depends(get_session),
) -> CapsuleInstallResponse:
    package_row = await _resolve_package_row(
        session,
        capsule_id=payload.capsule_id,
        version=payload.version,
    )

    existing_stmt = (
        select(capsule_installations)
        .where(
            capsule_installations.c.package_id == package_row["id"],
            capsule_installations.c.tenant_id == payload.tenant_id,
            capsule_installations.c.environment == payload.environment,
        )
        .limit(1)
    )
    existing = (await session.execute(existing_stmt)).mappings().first()
    now = datetime.utcnow()

    if existing and existing["status"] == "installed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Capsule already installed")

    merged_notes = payload.notes if payload.notes is not None else (existing.get("notes") if existing else None)

    if existing:
        await session.execute(
            capsule_installations.update()
            .where(capsule_installations.c.id == existing["id"])
            .values(
                status="installed",
                installed_at=now,
                installed_by=payload.installed_by,
                notes=merged_notes,
            )
        )
        installation_id = existing["id"]
    else:
        insert_stmt = (
            insert(capsule_installations)
            .returning(capsule_installations.c.id)
            .values(
                package_id=package_row["id"],
                tenant_id=payload.tenant_id,
                environment=payload.environment,
                installed_by=payload.installed_by,
                notes=payload.notes,
                status="installed",
            )
        )
        result = await session.execute(insert_stmt)
        installation_id = result.scalar_one()

    await session.commit()

    row = await _fetch_installation(session, installation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found after creation")
    return _installation_row_to_response(row)


@router.get("/installations", response_model=CapsuleInstallationListResponse)
async def list_installations(
    tenant_id: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> CapsuleInstallationListResponse:
    stmt = _installation_select()
    if tenant_id:
        stmt = stmt.where(capsule_installations.c.tenant_id == tenant_id)
    if environment:
        stmt = stmt.where(capsule_installations.c.environment == environment)
    stmt = stmt.order_by(capsule_installations.c.installed_at.desc())
    result = await session.execute(stmt)
    rows = result.mappings().all()
    installations = [_installation_row_to_response(row) for row in rows]
    return CapsuleInstallationListResponse(installations=installations)


@router.post(
    "/installations/{installation_id}/rollback",
    response_model=CapsuleInstallResponse,
    status_code=status.HTTP_200_OK,
)
async def rollback_installation(
    installation_id: int,
    payload: CapsuleRollbackRequest,
    session: AsyncSession = Depends(get_session),
) -> CapsuleInstallResponse:
    row = await _fetch_installation(session, installation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation not found")
    if row["status"] == "rolled_back":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Installation already rolled back")

    merged_notes = payload.notes if payload.notes is not None else row.get("notes")

    await session.execute(
        capsule_installations.update()
        .where(capsule_installations.c.id == installation_id)
        .values(
            status="rolled_back",
            notes=merged_notes,
            installed_by=payload.performed_by,
            installed_at=datetime.utcnow(),
        )
    )
    await session.commit()

    refreshed = await _fetch_installation(session, installation_id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Installation missing after update")
    return _installation_row_to_response(refreshed)
