"""
Capsule Evolution Engine
ML-powered analysis and improvement suggestions for Task Capsules.

Uses telemetry data and LLM analysis to evolve capsules over time.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict
import openai
import os

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai.api_key = OPENAI_API_KEY

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ExecutionTelemetry(BaseModel):
    """Telemetry from capsule execution."""
    capsule_id: str
    execution_id: str
    success: bool
    duration_seconds: float
    error_message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CapsuleMetrics(BaseModel):
    """Aggregated metrics for a capsule."""
    capsule_id: str
    total_executions: int
    success_rate: float
    average_duration: float
    failure_patterns: List[Dict[str, Any]]
    usage_contexts: List[str]


class ImprovementSuggestion(BaseModel):
    """AI-generated improvement suggestion."""
    capsule_id: str
    type: str  # 'optimization', 'error_handling', 'new_feature', 'refactoring'
    description: str
    rationale: str
    implementation_hints: List[str]
    confidence: float  # 0.0-1.0
    impact: str  # 'low', 'medium', 'high'
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EvolutionRequest(BaseModel):
    """Request for evolution analysis."""
    capsule_id: str
    capsule_definition: Dict[str, Any]
    time_window_days: int = 30


# ============================================================================
# IN-MEMORY STORAGE (Replace with real DB in production)
# ============================================================================

telemetry_store: Dict[str, List[ExecutionTelemetry]] = defaultdict(list)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Capsule Evolution Engine",
    description="ML-powered analysis and improvement for Task Capsules",
    version="1.0.0"
)

# ============================================================================
# TELEMETRY ANALYSIS
# ============================================================================

def analyze_telemetry(capsule_id: str, time_window_days: int = 30) -> CapsuleMetrics:
    """Analyze telemetry data for a capsule."""
    # Get telemetry from time window
    cutoff = datetime.utcnow() - timedelta(days=time_window_days)
    recent_telemetry = [
        t for t in telemetry_store.get(capsule_id, [])
        if t.timestamp >= cutoff
    ]
    
    if not recent_telemetry:
        return CapsuleMetrics(
            capsule_id=capsule_id,
            total_executions=0,
            success_rate=0.0,
            average_duration=0.0,
            failure_patterns=[],
            usage_contexts=[]
        )
    
    # Calculate metrics
    total = len(recent_telemetry)
    successes = sum(1 for t in recent_telemetry if t.success)
    success_rate = successes / total if total > 0 else 0.0
    
    durations = [t.duration_seconds for t in recent_telemetry]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    
    # Identify failure patterns
    failures = [t for t in recent_telemetry if not t.success]
    failure_patterns = []
    error_counts = defaultdict(int)
    
    for failure in failures:
        error_msg = failure.error_message or "Unknown error"
        error_counts[error_msg] += 1
    
    for error_msg, count in error_counts.items():
        failure_patterns.append({
            "error": error_msg,
            "count": count,
            "percentage": (count / len(failures)) * 100 if failures else 0
        })
    
    # Extract usage contexts
    contexts = list(set(
        json.dumps(t.context, sort_keys=True) for t in recent_telemetry if t.context
    ))
    
    return CapsuleMetrics(
        capsule_id=capsule_id,
        total_executions=total,
        success_rate=success_rate,
        average_duration=avg_duration,
        failure_patterns=failure_patterns,
        usage_contexts=contexts[:10]  # Top 10 contexts
    )


# ============================================================================
# LLM-POWERED IMPROVEMENT SUGGESTIONS
# ============================================================================

def generate_improvements_with_llm(
    capsule_definition: Dict[str, Any],
    metrics: CapsuleMetrics
) -> List[ImprovementSuggestion]:
    """Use GPT-4 to analyze capsule and suggest improvements."""
    prompt = f"""
You are an expert AI analyzing a Task Capsule to suggest improvements.

**Capsule Definition:**
```json
{json.dumps(capsule_definition, indent=2)}
```

**Performance Metrics (last 30 days):**
- Total Executions: {metrics.total_executions}
- Success Rate: {metrics.success_rate * 100:.1f}%
- Average Duration: {metrics.average_duration:.2f}s

**Failure Patterns:**
{json.dumps(metrics.failure_patterns, indent=2)}

**Task:**
Analyze this capsule and suggest 3-5 concrete improvements. For each suggestion, provide:
1. Type (optimization, error_handling, new_feature, refactoring)
2. Description (what to improve)
3. Rationale (why this matters)
4. Implementation hints (how to do it)
5. Confidence (0.0-1.0)
6. Impact (low, medium, high)

Return as JSON array of suggestions.
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert system architect analyzing Task Capsules."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse LLM response
        llm_output = response.choices[0].message.content
        
        # Extract JSON from response
        if "```json" in llm_output:
            llm_output = llm_output.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_output:
            llm_output = llm_output.split("```")[1].split("```")[0].strip()
        
        suggestions_data = json.loads(llm_output)
        
        # Convert to ImprovementSuggestion objects
        suggestions = []
        for data in suggestions_data:
            suggestions.append(ImprovementSuggestion(
                capsule_id=metrics.capsule_id,
                type=data.get("type", "optimization"),
                description=data.get("description", ""),
                rationale=data.get("rationale", ""),
                implementation_hints=data.get("implementation_hints", []),
                confidence=data.get("confidence", 0.5),
                impact=data.get("impact", "medium")
            ))
        
        logger.info(f"Generated {len(suggestions)} improvement suggestions for {metrics.capsule_id}")
        return suggestions
        
    except Exception as e:
        logger.error(f"LLM suggestion generation failed: {e}")
        # Fallback: rule-based suggestions
        return generate_fallback_suggestions(metrics)


def generate_fallback_suggestions(metrics: CapsuleMetrics) -> List[ImprovementSuggestion]:
    """Fallback rule-based suggestions when LLM fails."""
    suggestions = []
    
    # Low success rate → error handling
    if metrics.success_rate < 0.8:
        suggestions.append(ImprovementSuggestion(
            capsule_id=metrics.capsule_id,
            type="error_handling",
            description="Improve error handling and retry logic",
            rationale=f"Success rate is {metrics.success_rate * 100:.1f}%, below 80% threshold",
            implementation_hints=[
                "Add exponential backoff retry logic",
                "Implement circuit breaker pattern",
                "Add detailed error logging"
            ],
            confidence=0.9,
            impact="high"
        ))
    
    # Slow execution → optimization
    if metrics.average_duration > 10.0:
        suggestions.append(ImprovementSuggestion(
            capsule_id=metrics.capsule_id,
            type="optimization",
            description="Optimize execution performance",
            rationale=f"Average duration is {metrics.average_duration:.1f}s, consider optimization",
            implementation_hints=[
                "Profile code to identify bottlenecks",
                "Add caching for repeated operations",
                "Parallelize independent tasks"
            ],
            confidence=0.8,
            impact="medium"
        ))
    
    # Common failure patterns → specific fixes
    for pattern in metrics.failure_patterns[:3]:  # Top 3 failures
        if pattern["count"] > 5:
            suggestions.append(ImprovementSuggestion(
                capsule_id=metrics.capsule_id,
                type="error_handling",
                description=f"Handle common error: {pattern['error']}",
                rationale=f"This error occurred {pattern['count']} times ({pattern['percentage']:.1f}% of failures)",
                implementation_hints=[
                    "Add specific exception handling",
                    "Implement graceful degradation",
                    "Add user-friendly error messages"
                ],
                confidence=0.85,
                impact="high"
            ))
    
    return suggestions


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/telemetry")
def record_telemetry(telemetry: ExecutionTelemetry):
    """Record execution telemetry for a capsule."""
    telemetry_store[telemetry.capsule_id].append(telemetry)
    logger.info(f"Recorded telemetry for {telemetry.capsule_id}: success={telemetry.success}")
    
    return {"message": "Telemetry recorded", "capsule_id": telemetry.capsule_id}


@app.get("/metrics/{capsule_id}", response_model=CapsuleMetrics)
def get_capsule_metrics(capsule_id: str, days: int = 30):
    """Get aggregated metrics for a capsule."""
    metrics = analyze_telemetry(capsule_id, time_window_days=days)
    return metrics


@app.post("/evolve", response_model=List[ImprovementSuggestion])
def evolve_capsule(request: EvolutionRequest):
    """Analyze capsule and generate improvement suggestions."""
    # Get metrics
    metrics = analyze_telemetry(request.capsule_id, request.time_window_days)
    
    # Generate LLM-powered suggestions
    suggestions = generate_improvements_with_llm(request.capsule_definition, metrics)
    
    logger.info(f"Generated {len(suggestions)} suggestions for {request.capsule_id}")
    
    return suggestions


@app.get("/suggestions/{capsule_id}", response_model=List[ImprovementSuggestion])
def get_pending_suggestions(capsule_id: str):
    """Get pending improvement suggestions (placeholder for DB storage)."""
    # In production, this would query a database
    # For now, return empty list
    return []


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "evolution-engine",
        "telemetry_capsules": len(telemetry_store)
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)
