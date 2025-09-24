"""API endpoints for tool service."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["tools"])

TOOLS = [
    {"id": "plane", "name": "Plane.so", "status": "available"},
    {"id": "github", "name": "GitHub", "status": "available"},
]


@router.get("/adapters")
def list_adapters() -> dict[str, list[dict[str, str]]]:
    """Return available tool adapters (stub)."""

    return {"adapters": TOOLS}
