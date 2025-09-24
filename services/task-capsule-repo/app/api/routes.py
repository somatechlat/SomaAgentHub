"""API endpoints for task capsule repository."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["capsules"])

CAPSULES = [
    {
        "id": "project_bootstrap_planner",
        "version": "0.0.1",
        "summary": "Plan projects into executable task capsules.",
    }
]


@router.get("/")
def list_capsules() -> dict[str, list[dict[str, str]]]:
    """Return stub capsule catalog."""

    return {"capsules": CAPSULES}


@router.get("/{capsule_id}")
def read_capsule(capsule_id: str) -> dict[str, str]:
    """Return stub capsule record."""

    for capsule in CAPSULES:
        if capsule["id"] == capsule_id:
            return capsule
    return {"id": capsule_id, "status": "not-found"}
