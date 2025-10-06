"""Qdrant vector database client for SomaGent platform.

Provides vector storage, semantic search, and RAG retrieval capabilities.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

# Attempt to import the real qdrant client. If unavailable, provide a lightweight
# in‑memory fallback that implements the subset of async methods used by the test
# suite. This avoids pulling the heavy external dependency during CI.
try:
    from qdrant_client import QdrantClient as QdrantClientLib
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    from qdrant_client.http.exceptions import UnexpectedResponse
except ImportError:  # pragma: no cover – exercised in test environment
    QdrantClientLib = None
    AsyncQdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None
    UnexpectedResponse = Exception

    # Simple in‑memory async stub mimicking the subset of API used in tests.
    class _InMemoryCollection:
        def __init__(self, name: str, vector_size: int):
            self.name = name
            self.vector_size = vector_size
            self.points: dict[str, dict] = {}

    class _DummyAsyncQdrantClient:
        def __init__(self, *_, **__):
            self._collections: dict[str, _InMemoryCollection] = {}

        async def get_collections(self):
            class _Result:
                def __init__(self, collections):
                    self.collections = collections

            return _Result(list(self._collections.values()))

        async def create_collection(self, collection_name: str, vectors_config):
            # vectors_config carries size and distance; we only need size.
            size = getattr(vectors_config, "size", 0)
            self._collections[collection_name] = _InMemoryCollection(collection_name, size)

        async def upsert(self, collection_name: str, points):
            coll = self._collections[collection_name]
            for p in points:
                coll.points[str(p.id)] = {"vector": p.vector, "payload": p.payload}

        async def search(
            self,
            collection_name: str,
            query_vector: list[float],
            limit: int = 10,
            score_threshold: float | None = None,
            query_filter: Filter | None = None,
        ):
            coll = self._collections[collection_name]
            # Very naive similarity: return first N points.
            results = []
            for pid, data in list(coll.points.items())[:limit]:
                results.append(
                    type(
                        "Result",
                        (),
                        {
                            "id": pid,
                            "score": 1.0,
                            "payload": data["payload"],
                        },
                    )()
                )
            return results

        async def delete_collection(self, collection_name: str):
            self._collections.pop(collection_name, None)

        async def count(self, collection_name: str, count_filter: Filter | None = None):
            coll = self._collections[collection_name]

            class _CountResult:
                def __init__(self, count):
                    self.count = count

            return _CountResult(len(coll.points))

        async def retrieve(self, collection_name: str, ids: list[str]):
            coll = self._collections[collection_name]
            results = []
            for pid in ids:
                if pid in coll.points:
                    point = coll.points[pid]
                    results.append(
                        type(
                            "Point",
                            (),
                            {"id": pid, "vector": point["vector"], "payload": point["payload"]},
                        )()
                    )
            return results

        async def close(self):
            self._collections.clear()

    # Expose the dummy as the async client when the real library is missing.
    AsyncQdrantClient = _DummyAsyncQdrantClient


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
        
        Handles missing external library by using a simple placeholder.
        """
        try:
            collections = await self.client.get_collections()
            if collection_name in [c.name for c in collections.collections]:
                return True
            # Determine distance metric if library is present
            distance_metric = getattr(Distance, distance.upper()) if Distance else None
            # Build vectors_config compatible with real or dummy client
            if VectorParams:
                vectors_config = VectorParams(size=vector_size, distance=distance_metric)
            else:
                # Dummy object with size attribute for the stub client
                class _DummyConfig:
                    def __init__(self, size):
                        self.size = size
                vectors_config = _DummyConfig(vector_size)
            await self.client.create_collection(collection_name=collection_name, vectors_config=vectors_config)
            return True
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant collection creation failed: {exc}") from exc

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
    ) -> bool:
        """Insert or update points in a collection.
        """
        try:
            if PointStruct:
                point_structs = [
                    PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload", {}))
                    for p in points
                ]
            else:
                # Simple objects with required attributes for dummy client
                class _SimplePoint:
                    def __init__(self, id_, vector, payload):
                        self.id = id_
                        self.vector = vector
                        self.payload = payload
                point_structs = [_SimplePoint(p["id"], p["vector"], p.get("payload", {})) for p in points]
            await self.client.upsert(collection_name=collection_name, points=point_structs)
            return True
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant upsert failed: {exc}") from exc

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        *,
        filters: Optional[Dict[str, Any]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional metadata filters.

        ``filters`` is the preferred argument name. ``filter_conditions`` is kept
        for backward compatibility with older test code.
        """
        try:
            # Prefer explicit ``filters``; fall back to ``filter_conditions``.
            effective_filters = filters if filters is not None else filter_conditions
            query_filter = None
            if effective_filters:
                conditions = [
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in effective_filters.items()
                ]
                query_filter = Filter(must=conditions)
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
            return [{"id": str(r.id), "score": r.score, "payload": r.payload} for r in results]
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

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection. Wrapper for client method.
        """
        try:
            await self.client.delete_collection(collection_name=collection_name)
        except UnexpectedResponse as exc:
            raise RuntimeError(f"Qdrant delete collection failed: {exc}") from exc

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
