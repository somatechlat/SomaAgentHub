"""
RAG (Retrieval Augmented Generation) pipeline.

Retrieves relevant context from vector store and injects into prompts.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .vector_store import VectorStore, VectorDocument, get_vector_store
from .embedding_service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Retrieved context for RAG."""
    
    documents: List[VectorDocument]
    formatted_context: str
    total_tokens: int


class RAGPipeline:
    """Retrieval Augmented Generation pipeline."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_store: Vector store for retrieval
            embedding_service: Embedding service for queries
        """
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or get_embedding_service()
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.7
    ) -> RAGContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            filters: Optional metadata filters
            min_score: Minimum similarity score threshold
            
        Returns:
            RAGContext with formatted context
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search vector store
        documents = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
        
        # Filter by score
        documents = [doc for doc in documents if doc.score >= min_score]
        
        if not documents:
            logger.warning(f"No relevant documents found for query: {query[:50]}...")
            return RAGContext(
                documents=[],
                formatted_context="",
                total_tokens=0
            )
        
        # Format context
        formatted_context = self._format_context(documents)
        total_tokens = self._estimate_tokens(formatted_context)
        
        logger.info(f"Retrieved {len(documents)} documents ({total_tokens} tokens)")
        
        return RAGContext(
            documents=documents,
            formatted_context=formatted_context,
            total_tokens=total_tokens
        )
    
    def _format_context(self, documents: List[VectorDocument]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = ["# Retrieved Context\n"]
        
        for i, doc in enumerate(documents, 1):
            # Add document with metadata
            metadata_str = ", ".join(
                f"{k}: {v}" for k, v in doc.metadata.items()
                if k in ["source", "timestamp", "author"]
            )
            
            context_parts.append(
                f"\n## Document {i} (relevance: {doc.score:.2f})\n"
                f"Metadata: {metadata_str}\n\n"
                f"{doc.content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def augment_prompt(
        self,
        user_prompt: str,
        top_k: int = 3,
        max_context_tokens: int = 4000,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Augment user prompt with retrieved context.
        
        Args:
            user_prompt: Original user prompt
            top_k: Number of documents to retrieve
            max_context_tokens: Maximum tokens for context
            filters: Optional metadata filters
            
        Returns:
            Augmented prompt with context
        """
        # Retrieve context
        rag_context = self.retrieve_context(
            query=user_prompt,
            top_k=top_k,
            filters=filters
        )
        
        if not rag_context.documents:
            # No relevant context, return original prompt
            return user_prompt
        
        # Truncate context if too long
        formatted_context = rag_context.formatted_context
        if rag_context.total_tokens > max_context_tokens:
            # Truncate to max_context_tokens
            max_chars = max_context_tokens * 4
            formatted_context = formatted_context[:max_chars] + "\n\n[Context truncated...]"
        
        # Build augmented prompt
        augmented_prompt = f"""{formatted_context}

---

# User Query

{user_prompt}

Please answer the user's query using the information provided in the retrieved context above. If the context doesn't contain relevant information, please say so."""
        
        return augmented_prompt
    
    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        content_key: str = "content",
        metadata_keys: Optional[List[str]] = None
    ) -> int:
        """
        Index documents into vector store.
        
        Args:
            documents: List of document dictionaries
            content_key: Key for document content
            metadata_keys: Keys to include in metadata
            
        Returns:
            Number of documents indexed
        """
        metadata_keys = metadata_keys or ["source", "timestamp", "author"]
        
        vector_docs = []
        
        for doc in documents:
            content = doc.get(content_key, "")
            if not content:
                continue
            
            # Generate embedding
            embedding = self.embedding_service.embed_text(content)
            
            # Extract metadata
            metadata = {
                k: doc.get(k)
                for k in metadata_keys
                if k in doc
            }
            
            # Create vector document
            doc_id = doc.get("id") or self._generate_id(content)
            vector_docs.append(VectorDocument(
                id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata
            ))
        
        # Batch upsert
        if vector_docs:
            self.vector_store.upsert(vector_docs)
        
        logger.info(f"Indexed {len(vector_docs)} documents")
        return len(vector_docs)
    
    def _generate_id(self, content: str) -> str:
        """
        Generate document ID from content.
        
        Args:
            content: Document content
            
        Returns:
            Document ID
        """
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def search_conversations(
        self,
        query: str,
        user_id: str,
        top_k: int = 5
    ) -> List[VectorDocument]:
        """
        Search user's conversation history.
        
        Args:
            query: Search query
            user_id: User identifier
            top_k: Number of results
            
        Returns:
            Relevant conversation snippets
        """
        query_embedding = self.embedding_service.embed_text(query)
        
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters={"user_id": user_id, "type": "conversation"}
        )
        
        return results


# Global RAG pipeline instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create global RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def augment_with_context(
    prompt: str,
    top_k: int = 3,
    user_id: Optional[str] = None
) -> str:
    """
    Convenience function to augment prompt with RAG context.
    
    Args:
        prompt: User prompt
        top_k: Number of context documents
        user_id: Optional user ID for personalization
        
    Returns:
        Augmented prompt
    """
    pipeline = get_rag_pipeline()
    
    filters = {"user_id": user_id} if user_id else None
    
    return pipeline.augment_prompt(
        user_prompt=prompt,
        top_k=top_k,
        filters=filters
    )
