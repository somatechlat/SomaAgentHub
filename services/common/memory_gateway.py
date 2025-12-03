"""
Memory Gateway - Unified interface for Short-term (Redis) and Long-term (Qdrant) memory.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.common.redis_client import RedisClient
from services.common.qdrant_client import QdrantClient
from services.common.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

class MemoryGateway:
    def __init__(self):
        self.redis = RedisClient()
        self.qdrant = QdrantClient()
        self.llm = OpenAIProvider()

    async def create_short_term_memory(self, session_id: str, ttl_seconds: int = 3600):
        """Initialize short-term memory for a session."""
        key = f"stm:{session_id}:meta"
        await self.redis.set(key, json.dumps({"created_at": str(datetime.now()), "status": "active"}), ex=ttl_seconds)

    async def add_short_term_item(self, session_id: str, role: str, content: str):
        """Add an item to short-term memory (conversation history)."""
        key = f"stm:{session_id}:history"
        item = {"role": role, "content": content, "timestamp": str(datetime.now())}
        await self.redis.rpush(key, json.dumps(item))

    async def get_short_term_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent short-term history."""
        key = f"stm:{session_id}:history"
        items = await self.redis.lrange(key, -limit, -1)
        return [json.loads(i) for i in items]

    async def store_experience(self, agent_id: str, content: str, metadata: Dict[str, Any]):
        """Store long-term experience in Qdrant."""
        # Generate embedding
        embedding_result = await self.llm.generate_embedding(content)
        vector = embedding_result["embedding"]
        
        # Store in Qdrant
        await self.qdrant.upsert(
            collection_name="experiences",
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "agent_id": agent_id,
                    "content": content,
                    **metadata
                }
            }]
        )

    async def retrieve_context(self, agent_id: str, query: str, limit: int = 5) -> List[str]:
        """Retrieve relevant context from long-term memory."""
        embedding_result = await self.llm.generate_embedding(query)
        vector = embedding_result["embedding"]
        
        results = await self.qdrant.search(
            collection_name="experiences",
            query_vector=vector,
            limit=limit,
            query_filter={"must": [{"key": "agent_id", "match": {"value": agent_id}}]}
        )
        
        return [r.payload["content"] for r in results]
