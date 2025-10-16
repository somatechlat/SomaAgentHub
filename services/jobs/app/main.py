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
    """Execute background job by dispatching to task-specific handler.
    
    In production, integrate with:
    - Celery/Temporal for distributed task processing
    - Task queue (Redis/Kafka) for reliable delivery
    - Error handling and retry logic
    """
    try:
        JOB_STORE[job_id].status = "running"
        
        # REAL implementation: dispatch to task handler based on task name
        if task == "process_data":
            result = await _process_data(payload)
        elif task == "generate_report":
            result = await _generate_report(payload)
        elif task == "sync_external":
            result = await _sync_external(payload)
        else:
            raise ValueError(f"Unknown task type: {task}")
        
        JOB_STORE[job_id].status = "completed"
        JOB_STORE[job_id].result = result
    except Exception as exc:
        JOB_STORE[job_id].status = "failed"
        JOB_STORE[job_id].result = {"error": str(exc)}
    finally:
        # Publish result to Redis channel for observers
        import json
        await redis_client.publish(
            f"jobs:{job_id}",
            json.dumps({
                "status": JOB_STORE[job_id].status,
                "result": JOB_STORE[job_id].result
            })
        )


async def _process_data(payload: dict) -> dict:
    """Task handler: Process data payload."""
    # TODO: Implement real data processing logic
    # Examples: ETL, validation, transformation
    return {"processed": payload.get("source", "unknown"), "records": 0}


async def _generate_report(payload: dict) -> dict:
    """Task handler: Generate report."""
    # TODO: Implement real report generation
    # Examples: PDF generation, data aggregation, formatting
    return {"report_id": f"report-{payload.get('type', 'default')}", "page_count": 0}


async def _sync_external(payload: dict) -> dict:
    """Task handler: Sync with external system."""
    # TODO: Implement real external sync
    # Examples: API calls, webhook dispatching, data migration
    return {"synced": payload.get("target", "unknown"), "records": 0}

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
