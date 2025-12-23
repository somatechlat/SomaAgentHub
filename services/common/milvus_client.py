"""
Milvus client wrapper for vector storage (development: Milvus Lite; prod: HA Milvus).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class MilvusClient:
    """Lightweight wrapper around pymilvus for basic upsert/search."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection: str = "experiences",
    ):
        self.host = host or resolve_env("MILVUS_HOST", "milvus")
        self.port = port or int(resolve_env("MILVUS_PORT", "19530"))
        self.collection_name = resolve_env("MILVUS_COLLECTION", collection)
        self._ensure_connection()
        self.collection: Collection | None = None

    def _ensure_connection(self) -> None:
        alias = "default"
        if not utility.has_connection(alias):
            connections.connect(alias=alias, host=self.host, port=str(self.port))
            logger.info("Connected to Milvus at %s:%s", self.host, self.port)

    def _ensure_collection(self, dim: int) -> Collection:
        if utility.has_collection(self.collection_name):
            if self.collection is None:
                self.collection = Collection(self.collection_name)
            return self.collection

        id_field = FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            auto_id=False,
            max_length=64,
        )
        vector_field = FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=dim,
        )
        payload_field = FieldSchema(
            name="payload",
            dtype=DataType.JSON,
        )
        schema = CollectionSchema(
            fields=[id_field, vector_field, payload_field],
            description="Agent experiences",
        )
        collection = Collection(self.collection_name, schema)
        collection.create_index(
            field_name="vector",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 1024},
            },
        )
        collection.load()
        self.collection = collection
        logger.info("Created Milvus collection %s (dim=%s, metric=COSINE)", self.collection_name, dim)
        return collection

    def upsert(self, points: Sequence[dict[str, Any]]) -> None:
        if not points:
            return
        dim = len(points[0]["vector"])
        collection = self._ensure_collection(dim)
        ids = [p["id"] for p in points]
        vectors = [p["vector"] for p in points]
        payloads = [p.get("payload", {}) for p in points]
        collection.insert([ids, vectors, payloads])
        collection.flush()
        collection.load()
        logger.debug("Upserted %d points into %s", len(points), self.collection_name)

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        dim = len(query_vector)
        collection = self._ensure_collection(dim)
        expr = None
        if agent_id:
            expr = f'payload["agent_id"] == "{agent_id}"'
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        collection.load()
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["payload"],
        )
        hits: list[dict[str, Any]] = []
        for hit in results[0]:
            hits.append({"id": hit.id, "score": hit.distance, "payload": hit.entity.get("payload", {})})
        return hits
