"""Qdrant vector database client for SomaGent platform.

Provides vector storage, semantic search, and RAG retrieval capabilities.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient as QdrantClientLib
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from qdrant_client.http.exceptions import UnexpectedResponse
except ImportError:
    QdrantClientLib = None
    AsyncQdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    UnexpectedResponse = Exception


class QdrantClient:
    """Async Qdrant client for vector storage and search."""

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize Qdrant client.
        
        Args:
            url: Qdrant server URL (e.g., http://qdrant:6333)
            api_key: API key for authentication (optional)
            timeout: Request timeout in seconds
        """
        if AsyncQdrantClient is None:
            raise RuntimeError("qdrant-client not installed. Run: pip install qdrant-client")
        
        self.url = url
        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
            timeout=timeout,
        )

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 768,
        distance: str = "Cosine",
    ) -> bool:
        """Create a new collection for vectors.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors (default: 768 for text-embedding-ada-002)
            distance: Distance metric ("Cosine", "Euclid", "Dot")
            
        Returns:
            True if successful
        """
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            if collection_name in [c.name for c in collections.collections]:
                return True
            
            # Create collection
            distance_metric = getattr(Distance, distance.upper())
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_metric,
                ),
            )
            return True
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant collection creation failed: {exc}") from exc

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
    ) -> bool:
        """Insert or update points in a collection.
        
        Args:
            collection_name: Name of the collection
            points: List of points with id, vector, and payload
                Example: [
                    {
                        "id": "uuid-1",
                        "vector": [0.1, 0.2, ...],
                        "payload": {"text": "...", "metadata": {...}}
                    }
                ]
                
        Returns:
            True if successful
        """
        try:
            point_structs = [
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
                for p in points
            ]
            
            await self.client.upsert(
                collection_name=collection_name,
                points=point_structs,
            )
            return True
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant upsert failed: {exc}") from exc

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score (optional)
            filters: Metadata filters (optional)
                Example: {"tenant_id": "demo", "user_id": "user-123"}
                
        Returns:
            List of search results with id, score, and payload
        """
        try:
            # Build filter
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filters.items()
                ]
                query_filter = Filter(must=conditions)
            
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
            
            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant search failed: {exc}") from exc

    async def get_point(
        self,
        collection_name: str,
        point_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a specific point by ID.
        
        Returns:
            Point data with id, vector, and payload, or None if not found
        """
        try:
            result = await self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
            )
            
            if not result:
                return None
            
            point = result[0]
            return {
                "id": str(point.id),
                "vector": point.vector,
                "payload": point.payload,
            }
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant retrieve failed: {exc}") from exc

    async def delete_points(
        self,
        collection_name: str,
        point_ids: List[str],
    ) -> bool:
        """Delete points from a collection.
        
        Args:
            collection_name: Name of the collection
            point_ids: List of point IDs to delete
            
        Returns:
            True if successful
        """
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids,
            )
            return True
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant delete failed: {exc}") from exc

    async def count_points(
        self,
        collection_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count points in a collection with optional filters."""
        try:
            # Build filter
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filters.items()
                ]
                query_filter = Filter(must=conditions)
            
            result = await self.client.count(
                collection_name=collection_name,
                count_filter=query_filter,
            )
            return result.count
            
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant count failed: {exc}") from exc

    async def health_check(self) -> bool:
        """Check if Qdrant server is accessible."""
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close Qdrant client connection."""
        await self.client.close()


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client from environment variables.
    
    Required environment variables:
        QDRANT_URL: Qdrant server URL
        QDRANT_API_KEY: API key (optional)
        QDRANT_TIMEOUT: Request timeout in seconds (optional, default: 30)
    """
    url = os.getenv("QDRANT_URL")
    if not url:
        raise RuntimeError("QDRANT_URL environment variable not set")
    
    api_key = os.getenv("QDRANT_API_KEY")
    timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))
    
    return QdrantClient(
        url=url,
        api_key=api_key,
        timeout=timeout,
    )
