# Sprint: SLM Service Real Integration

**Date:** October 5, 2025  
**Objective**: Replace echo/stub responses with real SLM provider integrations (OpenAI, Anthropic, local models).

## Current State
- ✅ SLM service exists with health endpoints
- ✅ Provider abstraction layer defined
- ❌ All providers return echo/stub responses
- ❌ No streaming implementation
- ❌ No real API calls to providers

## Tasks

### 1. OpenAI Provider Implementation
- Add `openai` library dependency
- Implement real chat completions API calls
- Add streaming support with SSE
- Handle rate limits and retries
- Add cost tracking per request

### 2. Anthropic Provider Implementation
- Add `anthropic` library dependency
- Implement Claude API integration
- Add streaming support
- Handle model selection (claude-3-opus, sonnet, haiku)

### 3. Local Model Provider
- Add `transformers` or `vllm` integration
- Support local model serving
- Implement batching for efficiency
- Add GPU detection and allocation

### 4. Provider Router
- Implement model selection logic
- Add fallback chains (primary → backup)
- Track provider health and latency
- Emit metrics per provider

## Files to Modify
- `services/slm-service/app/providers/openai_provider.py`
- `services/slm-service/app/providers/anthropic_provider.py`
- `services/slm-service/app/providers/local_provider.py`
- `services/slm-service/app/main.py` (remove TODO comments)
- `services/orchestrator/app/api/conversation.py` (wire SLM calls)

## Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export SLM_DEFAULT_PROVIDER="openai"
export SLM_DEFAULT_MODEL="gpt-4"
```

## Success Criteria
- ✅ Real completions from OpenAI/Anthropic
- ✅ Streaming responses work end-to-end
- ✅ Cost tracking per request
- ✅ Provider failover works
- ✅ No echo/stub responses remain

## Owner
AI Runtime team

## Status
**Not started** – TODO comments in conversation.py
