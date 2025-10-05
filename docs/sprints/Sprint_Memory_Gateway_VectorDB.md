# Sprint: Memory Gateway Vector Database

**Date:** October 5, 2025  
**Objective**: Replace in-memory dict stub with real vector database (Qdrant) for memory persistence and RAG retrieval.

## Current State
- ✅ Memory Gateway service exists
- ✅ API endpoints defined
- ❌ Using in-memory dict (`MEMORY_STORE: dict[str, Any] = {}`)
- ❌ RAG endpoint echoes query (dummy implementation)
- ❌ No vector embeddings
- ❌ No semantic search

## Tasks

### 1. Qdrant Integration
- Add `qdrant-client` library
- Implement Qdrant connection and collection management
- Create collections for: memories, conversations, documents
- Add health checks and reconnection logic

### 2. Embedding Generation
- Wire SLM service `/v1/embeddings` endpoint
- Generate embeddings for all stored memories
- Cache embeddings in Qdrant vectors
- Support multiple embedding models

### 3. RAG Retrieval Implementation
- Implement semantic search with cosine similarity
- Add hybrid search (vector + keyword)
- Return top-k results with scores
- Include source attribution

### 4. Memory Persistence
- Replace `/v1/remember` to store in Qdrant
- Add metadata (timestamp, user, session)
- Implement memory expiration (TTL)
- Support memory updates and deletions

### 5. Conversation History
- Store conversation turns in Qdrant
- Implement session-based retrieval
- Add conversation summarization
- Support multi-turn context window

## Files to Modify
- `services/memory-gateway/app/main.py` (replace dict with Qdrant)
- `services/common/qdrant_client.py` (create new shared client)
- `services/common/embeddings.py` (embedding generation helper)

## Qdrant Collections
```
memories
  - id: uuid
  - vector: [768-dim embedding]
  - payload: {content, user_id, tenant_id, timestamp, metadata}

conversations
  - id: session_id
  - vector: [conversation summary embedding]
  - payload: {messages[], participants, created_at, metadata}
```

## Environment Variables
```bash
export QDRANT_URL="http://qdrant:6333"
export QDRANT_API_KEY="..."
export QDRANT_COLLECTION_MEMORIES="memories"
export QDRANT_COLLECTION_CONVERSATIONS="conversations"
export EMBEDDING_MODEL="text-embedding-3-small"
```

## Success Criteria
- ✅ Memories persist across restarts
- ✅ RAG returns semantically relevant results
- ✅ Conversation history retrieved correctly
- ✅ Search latency <100ms (p95)
- ✅ No in-memory dict remains

## Owner
AI/Data team

## Status
**Not started** – in-memory stub currently
