"""
Vector store integration for semantic search and RAG.

Supports multiple vector database backends:
- Pinecone (cloud)
- Qdrant (self-hosted)
- ChromaDB (local)
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class VectorBackend(str, Enum):
    """Supported vector database backends."""
    
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    CHROMA = "chroma"


@dataclass
class VectorDocument:
    """Document with embedding."""
    
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    score: float = 0.0  # Similarity score


class VectorStore:
    """Unified interface for vector databases."""
    
    def __init__(
        self,
        backend: VectorBackend = VectorBackend.QDRANT,
        collection_name: str = "somaagent-vectors",
        dimension: int = 1536  # OpenAI ada-002 dimension
    ):
        """
        Initialize vector store.
        
        Args:
            backend: Vector database backend
            collection_name: Collection/index name
            dimension: Embedding dimension
        """
        self.backend = backend
        self.collection_name = collection_name
        self.dimension = dimension
        self.client = self._init_client()
    
    def _init_client(self) -> Any:
        """Initialize backend client."""
        if self.backend == VectorBackend.PINECONE:
            import pinecone
            
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            
            pinecone.init(api_key=api_key, environment=environment)
            
            # Create index if not exists
            if self.collection_name not in pinecone.list_indexes():
                pinecone.create_index(
                    self.collection_name,
                    dimension=self.dimension,
                    metric="cosine"
                )
            
            return pinecone.Index(self.collection_name)
        
        elif self.backend == VectorBackend.QDRANT:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            host = os.getenv("QDRANT_HOST", "localhost")
            port = int(os.getenv("QDRANT_PORT", 6333))
            
            client = QdrantClient(host=host, port=port)
            
            # Create collection if not exists
            try:
                client.get_collection(self.collection_name)
            except Exception:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
            
            return client
        
        elif self.backend == VectorBackend.CHROMA:
            import chromadb
            
            client = chromadb.Client()
            collection = client.get_or_create_collection(self.collection_name)
            return collection
        
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
    
    def upsert(
        self,
        documents: List[VectorDocument]
    ) -> None:
        """
        Insert or update documents.
        
        Args:
            documents: List of documents to upsert
        """
        if self.backend == VectorBackend.PINECONE:
            vectors = [
                (doc.id, doc.embedding, doc.metadata)
                for doc in documents
            ]
            self.client.upsert(vectors=vectors)
        
        elif self.backend == VectorBackend.QDRANT:
            from qdrant_client.models import PointStruct
            
            points = [
                PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload={**doc.metadata, "content": doc.content}
                )
                for doc in documents
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        elif self.backend == VectorBackend.CHROMA:
            self.client.add(
                ids=[doc.id for doc in documents],
                embeddings=[doc.embedding for doc in documents],
                metadatas=[doc.metadata for doc in documents],
                documents=[doc.content for doc in documents]
            )
        
        logger.info(f"Upserted {len(documents)} documents to {self.backend}")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorDocument]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        if self.backend == VectorBackend.PINECONE:
            results = self.client.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filters,
                include_metadata=True
            )
            
            return [
                VectorDocument(
                    id=match.id,
                    content=match.metadata.get("content", ""),
                    embedding=[],  # Not returned by Pinecone
                    metadata=match.metadata,
                    score=match.score
                )
                for match in results.matches
            ]
        
        elif self.backend == VectorBackend.QDRANT:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build filter
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
                query_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter
            )
            
            return [
                VectorDocument(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    embedding=[],
                    metadata={k: v for k, v in hit.payload.items() if k != "content"},
                    score=hit.score
                )
                for hit in results
            ]
        
        elif self.backend == VectorBackend.CHROMA:
            results = self.client.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            documents = []
            for i in range(len(results['ids'][0])):
                documents.append(VectorDocument(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    embedding=[],
                    metadata=results['metadatas'][0][i],
                    score=1 - results['distances'][0][i]  # Convert distance to similarity
                ))
            
            return documents
        
        return []
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        """
        if self.backend == VectorBackend.PINECONE:
            self.client.delete(ids=ids)
        
        elif self.backend == VectorBackend.QDRANT:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=ids
            )
        
        elif self.backend == VectorBackend.CHROMA:
            self.client.delete(ids=ids)
        
        logger.info(f"Deleted {len(ids)} documents from {self.backend}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Statistics dictionary
        """
        if self.backend == VectorBackend.PINECONE:
            stats = self.client.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension
            }
        
        elif self.backend == VectorBackend.QDRANT:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_vectors": info.points_count,
                "dimension": info.config.params.vectors.size
            }
        
        elif self.backend == VectorBackend.CHROMA:
            count = self.client.count()
            return {
                "total_vectors": count,
                "dimension": self.dimension
            }
        
        return {}


class HybridSearch:
    """Hybrid search combining vector and keyword search."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize hybrid search.
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
    
    def search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        vector_weight: float = 0.7
    ) -> List[VectorDocument]:
        """
        Hybrid search with vector and text.
        
        Args:
            query_embedding: Query embedding
            query_text: Query text for keyword matching
            top_k: Number of results
            vector_weight: Weight for vector similarity (0-1)
            
        Returns:
            Ranked results combining both methods
        """
        # Vector search
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2)
        
        # Keyword boosting
        keyword_weight = 1 - vector_weight
        query_terms = set(query_text.lower().split())
        
        for doc in vector_results:
            # Calculate keyword match score
            doc_terms = set(doc.content.lower().split())
            keyword_score = len(query_terms & doc_terms) / max(len(query_terms), 1)
            
            # Combine scores
            doc.score = (
                vector_weight * doc.score +
                keyword_weight * keyword_score
            )
        
        # Re-rank and return top_k
        vector_results.sort(key=lambda x: x.score, reverse=True)
        return vector_results[:top_k]


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store."""
    global _vector_store
    if _vector_store is None:
        backend = VectorBackend(os.getenv("VECTOR_BACKEND", "qdrant"))
        _vector_store = VectorStore(backend=backend)
    return _vector_store
