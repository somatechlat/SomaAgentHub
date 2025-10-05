"""Streaming conversation endpoints for orchestrator."""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram

router = APIRouter(prefix="/v1/conversation", tags=["conversation"])

# Prometheus metrics
CONVERSATION_REQUESTS = Counter(
    "orchestrator_requests_total",
    "Total conversation requests",
    labelnames=("route", "decision"),
)

CONVERSATION_LATENCY = Histogram(
    "orchestrator_conversation_latency_seconds",
    "Conversation endpoint latency",
    labelnames=("route",),
)


class ConversationStepRequest(BaseModel):
    session_id: str
    tenant: str
    user: str
    prompt: str
    metadata: dict = {}


class ConversationStepResponse(BaseModel):
    session_id: str
    response: str
    constitution_hash: str | None = None
    policy_score: float | None = None


async def _emit_conversation_event(session_id: str, tenant: str, event_type: str, data: dict) -> None:
    """Emit conversation event to Kafka topic."""
    try:
        from services.common.kafka_client import get_kafka_client
        kafka_client = get_kafka_client()
        
        # Ensure producer is started
        if kafka_client._producer is None:
            await kafka_client.start()
        
        await kafka_client.send_event(
            topic="conversation.events",
            event={
                "session_id": session_id,
                "tenant": tenant,
                "event_type": event_type,
                "timestamp": time.time(),
                "data": data,
            },
            key=session_id,
        )
    except Exception as exc:
        # Log error but don't block request
        print(f"[KAFKA_ERROR] Failed to emit conversation event: {exc}")
        event = {
            "session_id": session_id,
            "tenant": tenant,
            "event_type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        print(f"[CONVERSATION_EVENT] {json.dumps(event)}")


@router.post("/step", response_model=ConversationStepResponse)
async def conversation_step(
    req: ConversationStepRequest,
    x_policy_decision: str | None = Header(None),
    x_policy_score: str | None = Header(None),
    x_constitution_hash: str | None = Header(None),
) -> ConversationStepResponse:
    """Synchronous conversation turn with policy enforcement."""
    start_time = time.perf_counter()
    
    # Validate policy headers
    if x_policy_decision and x_policy_decision.lower() == "deny":
        CONVERSATION_REQUESTS.labels(route="step", decision="deny").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy evaluation denied this request",
        )
    
    CONVERSATION_REQUESTS.labels(route="step", decision="allow").inc()
    
    # Emit conversation event
    await _emit_conversation_event(
        req.session_id,
        req.tenant,
        "conversation.step",
        {
            "prompt": req.prompt,
            "user": req.user,
            "policy_score": float(x_policy_score) if x_policy_score else None,
        },
    )
    
    # TODO: Call SLM service via queue/sync endpoint
    response_text = f"Echo: {req.prompt[:50]}..."
    
    elapsed = time.perf_counter() - start_time
    CONVERSATION_LATENCY.labels(route="step").observe(elapsed)
    
    return ConversationStepResponse(
        session_id=req.session_id,
        response=response_text,
        constitution_hash=x_constitution_hash,
        policy_score=float(x_policy_score) if x_policy_score else None,
    )


async def _stream_conversation(
    session_id: str,
    tenant: str,
    prompt: str,
    constitution_hash: str | None,
    policy_score: str | None,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for conversation."""
    # Emit start event
    await _emit_conversation_event(
        session_id, tenant, "conversation.stream_start", {"prompt": prompt}
    )
    
    # Use OpenAI provider for real streaming completions
    try:
        from services.common.openai_provider import get_openai_provider
        openai_provider = get_openai_provider()
        
        chunk_count = 0
        async for chunk in openai_provider.complete_stream(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        ):
            chunk_count += 1
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
        # Emit completion event
        await _emit_conversation_event(
            session_id, tenant, "conversation.stream_complete", {"chunks": chunk_count}
        )
    except Exception as exc:
        # Fallback to echo response if OpenAI unavailable
        print(f"[OPENAI_ERROR] Streaming failed, using fallback: {exc}")
        chunks = ["Hello", " from", " orchestrator", " streaming", " endpoint!"]
        for chunk in chunks:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.1)
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        
        # Emit completion event
        await _emit_conversation_event(
            session_id, tenant, "conversation.stream_complete", {"chunks": len(chunks)}
        )


@router.post("/stream")
async def conversation_stream(
    req: ConversationStepRequest,
    x_policy_decision: str | None = Header(None),
    x_policy_score: str | None = Header(None),
    x_constitution_hash: str | None = Header(None),
) -> StreamingResponse:
    """Streaming conversation endpoint using Server-Sent Events."""
    start_time = time.perf_counter()
    
    # Validate policy headers
    if x_policy_decision and x_policy_decision.lower() == "deny":
        CONVERSATION_REQUESTS.labels(route="stream", decision="deny").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy evaluation denied this request",
        )
    
    CONVERSATION_REQUESTS.labels(route="stream", decision="allow").inc()
    
    # Record latency at stream start
    elapsed = time.perf_counter() - start_time
    CONVERSATION_LATENCY.labels(route="stream").observe(elapsed)
    
    return StreamingResponse(
        _stream_conversation(
            req.session_id,
            req.tenant,
            req.prompt,
            x_constitution_hash,
            x_policy_score,
        ),
        media_type="text/event-stream",
    )
