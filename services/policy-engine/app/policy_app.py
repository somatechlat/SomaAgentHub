from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from typing import Any

app = FastAPI(
    title="SomaAgent Policy Engine",
    version="1.0.0",
    description="OPA-based Policy Enforcement Point (PEP).",
)

from services.common.opa_client import get_opa_client

class EvalRequest(BaseModel):
    session_id: str
    tenant: str
    user: str
    prompt: str
    role: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvalResponse(BaseModel):
    allowed: bool
    reasons: list[str]

@app.post("/v1/evaluate", response_model=EvalResponse)
async def evaluate(req: EvalRequest):
    """
    Evaluate a request against OPA policies.
    Real implementation using OPAClient.
    """
    client = get_opa_client()
    
    # Construct input for OPA
    input_data = {
        "user": req.user,
        "tenant": req.tenant,
        "action": "evaluate_prompt", # Example action
        "resource": "llm",
        "context": {
            "prompt": req.prompt,
            "role": req.role,
            "metadata": req.metadata,
            "session_id": req.session_id
        }
    }
    
    try:
        # Call OPA
        # Assuming a default policy path for prompt evaluation
        result = await client.evaluate_policy(
            policy_path="somagent/prompt_policy",
            input_data=input_data
        )
        
        allowed = result.get("allowed", False)
        reasons = result.get("reasons", [])
        if not allowed and not reasons:
            reasons = ["Policy denied request"]
            
        return EvalResponse(allowed=allowed, reasons=reasons)
        
    except Exception as e:
        # Fail closed on error
        return EvalResponse(allowed=False, reasons=[f"Policy evaluation failed: {str(e)}"])

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "policy-engine", "backend": "opa"}

@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
