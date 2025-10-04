from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from pydantic import BaseModel, Field
import uuid
import os
import redis.asyncio as aioredis
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Jobs Service")

# Redis connection (reuse same host/port as other services)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = aioredis.from_url(REDIS_URL)

# Simple counter for jobs service metrics
JOBS_REQUESTS = Counter("jobs_requests_total", "Total requests to Jobs service")

class JobCreate(BaseModel):
    task: str = Field(..., description="Name of the task to run")
    payload: dict = Field(default_factory=dict, description="Arbitrary payload for the job")

class JobStatus(BaseModel):
    id: str
    status: str
    result: dict | None = None

# In‑memory store for job metadata (for demo purposes)
JOB_STORE: dict[str, JobStatus] = {}

async def _run_job(job_id: str, task: str, payload: dict):
    """Simulated background job – replace with real worker logic later."""
    # Mark as running
    JOB_STORE[job_id].status = "running"
    # Simulate work (e.g., sleep)
    import asyncio
    await asyncio.sleep(2)
    # Dummy result
    result = {"message": f"Task {task} completed", "payload": payload}
    JOB_STORE[job_id].status = "completed"
    JOB_STORE[job_id].result = result
    # Publish result to a Redis channel for observers (optional)
    await redis_client.publish(f"jobs:{job_id}", str(result))

@app.post("/v1/jobs", response_model=JobStatus)
async def create_job(job: JobCreate, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = JobStatus(id=job_id, status="queued")
    # Schedule background execution
    background_tasks.add_task(_run_job, job_id, job.task, job.payload)
    return JOB_STORE[job_id]

@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOB_STORE[job_id]

@app.get("/health", tags=["system"])
async def health() -> Response:
    """Simple health check used by Kubernetes liveness/readiness probes."""
    return Response(content="OK", media_type="text/plain")

@app.get("/metrics", response_class=Response)
async def metrics():
    """Expose Prometheus metrics for the Jobs service."""
    JOBS_REQUESTS.inc()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
