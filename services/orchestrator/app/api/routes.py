"""HTTP routes exposed by the orchestrator."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse
import asyncio
import os
import json
import httpx
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from typing import AsyncGenerator, Dict, Any
from uuid import uuid4

router = APIRouter(prefix="/v1", tags=["orchestrator"])

# --- configuration ---
POLICY_ENGINE_URL = os.getenv("POLICY_ENGINE_URL", "http://localhost:8100/v1/evaluate")
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8002/v1/tokens/issue")

# ---------------------------------------------------------------------------
# Helper: publish a message to a Kafka topic (real, not mocked).
# ---------------------------------------------------------------------------
async def _publish_kafka(topic: str, payload: dict) -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap:
        print(f"[WARN] Kafka not configured – dropping {topic} event:", payload)
        return
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap.split(","))
    await producer.start()
    try:
        await producer.send_and_wait(topic, json.dumps(payload).encode("utf-8"))
    finally:
        await producer.stop()

# ---------------------------------------------------------------------------
# Background consumer that logs audit / conversation events (skeleton).
# ---------------------------------------------------------------------------
async def _audit_event_consumer() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap:
        print("[INFO] No Kafka broker – audit consumer disabled.")
        return
    consumer = AIOKafkaConsumer(
        "gateway.audit",
        "conversation.events",
        bootstrap_servers=bootstrap.split(","),
        group_id="orchestrator_audit_consumer",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
                print(f"[AUDIT] topic={msg.topic} data={data}")
            except Exception as exc:
                print("[ERROR] failed to decode audit msg", exc)
    finally:
        await consumer.stop()

# ---------------------------------------------------------------------------
# FastAPI startup hook – fire‑and‑forget the audit consumer.
# ---------------------------------------------------------------------------
@router.on_event("startup")
async def _startup_background_tasks() -> None:
    asyncio.create_task(_audit_event_consumer())

# ---------------------------------------------------------------------------
# Session start – real policy check, real token issuance, real SLM publish.
# ---------------------------------------------------------------------------
async def _publish_slm_request(payload: dict) -> None:
    await _publish_kafka("slm.requests", payload)

@router.post("/sessions/start")
async def start_session(
    payload: dict | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    """Start a session, validate policy, issue a JWT, and emit an SLM request.
    Expected payload keys (minimum):
        session_id, tenant, user, prompt, role
    """
    payload = payload or {}

    # -------------------------------------------------------------------
    # 1️⃣ Policy evaluation (real call)
    # -------------------------------------------------------------------
    try:
        async with httpx.AsyncClient() as client:
            eval_resp = await client.post(POLICY_ENGINE_URL, json=payload, timeout=5.0)
            policy_result = eval_resp.json()
    except Exception as exc:
        policy_result = {"allowed": False, "score": 0.0, "reasons": {"error": str(exc)}}

    # -------------------------------------------------------------------
    # 2. Issue a JWT via the Identity Service (real call).
    # -------------------------------------------------------------------
    token_response = None
    try:
        token_req = {
            "user_id": payload.get("user"),
            "tenant_id": payload.get("tenant"),
            "capabilities": ["session:start"],
            "mfa_code": payload.get("mfa_code", ""),
        }
        async with httpx.AsyncClient() as client:
            tok_resp = await client.post(IDENTITY_SERVICE_URL, json=token_req, timeout=5.0)
            token_response = tok_resp.json()
    except Exception as exc:
        token_response = {"error": f"identity token issuance failed: {exc}"}

    # -------------------------------------------------------------------
    # 3. Schedule a background SLM request publish (real Kafka).
    # -------------------------------------------------------------------
    if background_tasks is not None:
        background_tasks.add_task(_publish_slm_request, payload)

    return {
        "session_id": payload.get("session_id", "stub-session"),
        "policy": policy_result,
        "token": token_response,
        "status": "accepted",
    }

# ---------------------------------------------------------------------------
# Turn streaming – emit SSE events and also publish them to Kafka topics.
# ---------------------------------------------------------------------------
async def _turn_event_generator(session_id: str) -> AsyncGenerator[str, None]:
    events = [
        {"event": "turn_started", "session_id": session_id, "detail": "session initialized"},
        {"event": "policy_applied", "session_id": session_id, "detail": "policy evaluated"},
        {"event": "turn_completed", "session_id": session_id, "detail": "response ready"},
    ]
    for ev in events:
        # Publish to audit & conversation topics (real).
        await _publish_kafka("gateway.audit", ev)
        await _publish_kafka("conversation.events", ev)
        yield f"data: {json.dumps(ev)}\n\n"
        await asyncio.sleep(0.1)

@router.get("/turn/{session_id}")
async def turn_stream(session_id: str):
    """Stream turn‑loop events as Server‑Sent Events (SSE) while publishing
    audit and conversation events to Kafka.
    """
    return StreamingResponse(_turn_event_generator(session_id), media_type="text/event-stream")

# ---------------------------------------------------------------------------
# Sprint 3 – Marketplace Alpha (real minimal API)
# ---------------------------------------------------------------------------
# In‑memory stores (for demo purposes – real implementation would use a DB)
CAPSULES: Dict[str, Dict[str, Any]] = {}

@router.post("/marketplace/publish")
async def publish_capsule(payload: dict) -> dict:
    """Publish a capsule (memory bundle) to the marketplace.
    A real implementation would verify signatures, store in persistent storage,
    and index for search. Here we keep it simple and store in an in‑memory dict.
    """
    capsule_id = str(uuid4())
    CAPSULES[capsule_id] = payload
    return {"capsule_id": capsule_id, "status": "published"}

@router.get("/marketplace/capsules")
async def list_capsules() -> list:
    """Return a list of published capsules (metadata only)."""
    return [{"capsule_id": cid, "metadata": data} for cid, data in CAPSULES.items()]

# ---------------------------------------------------------------------------
# Sprint 4 – Durable Jobs (simple async job processing)
# ---------------------------------------------------------------------------
JOBS: Dict[str, Dict[str, Any]] = {}

async def _process_job(job_id: str, payload: dict) -> None:
    """Simulate a long‑running job. Updates JOBS dict when done."""
    # Simulate work (e.g., Temporal workflow would be started here)
    await asyncio.sleep(2)  # pretend the job takes 2 seconds
    JOBS[job_id]["status"] = "completed"
    JOBS[job_id]["result"] = {"message": "Job finished", "payload": payload}

@router.post("/jobs/start")
async def start_job(payload: dict) -> dict:
    """Start a background job and return a job identifier.
    In a full system this would invoke Temporal or another workflow engine.
    """
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "running", "payload": payload}
    # Fire‑and‑forget the simulated job processor
    asyncio.create_task(_process_job(job_id, payload))
    return {"job_id": job_id, "status": "running"}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Retrieve the status (and result if completed) of a job."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}

# ---------------------------------------------------------------------------
# New health check endpoint (Sprint 5 – Hardening & Launch Readiness)
# ---------------------------------------------------------------------------
@router.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """Simple liveness probe – returns OK if the app is running.
    Future extensions may check DB/Kafka connectivity.
    """
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Analytics endpoint – capsule statistics (Sprint 7 – Analytics & Insights)
# ---------------------------------------------------------------------------
@router.get("/analytics/capsules")
async def analytics_capsules() -> dict:
    """Return basic analytics for the in‑memory capsule store.
    For now we provide a simple count; later this can be expanded with
    usage, performance, and billing metrics.
    """
    count = len(CAPSULES)
    return {"total_capsules": count}
