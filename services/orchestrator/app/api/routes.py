"""HTTP routes exposed by the orchestrator."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["orchestrator"])


@router.post("/sessions/start")
def start_session(payload: dict | None = None) -> dict[str, str]:
    """Stub endpoint for initiating an orchestration session."""

    _ = payload or {}
    return {"session_id": "stub-session", "status": "accepted"}


@router.post("/sessions/{session_id}/complete")
def complete_session(session_id: str) -> dict[str, str]:
    """Mark a session complete (placeholder until orchestration logic lands)."""

    return {"session_id": session_id, "status": "completed"}
