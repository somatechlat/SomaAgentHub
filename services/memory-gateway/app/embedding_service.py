"""
Embedding service for text vectorization.

Supports multiple embedding models:
- OpenAI ada-002
- Sentence Transformers (local)
- Cohere embeddings
"""

import logging
import os
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel(str, Enum):
    """Supported embedding models."""

    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    SENTENCE_BERT = "all-MiniLM-L6-v2"
    COHERE_ENGLISH = "embed-english-v3.0"


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(
        self,
        model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002,
        batch_size: int = 100,
    ):
        """
        Initialize embedding service.

        Args:
            model: Embedding model to use
            batch_size: Batch size for bulk operations
        """
        self.model = model
        self.batch_size = batch_size
        self.client = self._init_client()

    def _init_client(self) -> any:
        """Initialize embedding model client."""
        if self.model.startswith("text-embedding"):
            # OpenAI embeddings
            import openai

            openai.api_key = os.getenv("OPENAI_API_KEY")
            return openai

        elif self.model == EmbeddingModel.SENTENCE_BERT:
            # Local sentence transformers
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.model.value)

        elif self.model == EmbeddingModel.COHERE_ENGLISH:
            # Cohere embeddings
            import cohere

            api_key = os.getenv("COHERE_API_KEY")
            return cohere.Client(api_key)

        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text.strip():
            # Return zero vector for empty text
            return self._zero_vector()

        embeddings = self.embed_batch([text])
        return embeddings[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter empty texts
        non_empty_texts = [t for t in texts if t.strip()]
        if not non_empty_texts:
            return [self._zero_vector() for _ in texts]

        if self.model.startswith("text-embedding"):
            # OpenAI embeddings
            return self._embed_openai(non_empty_texts)

        elif self.model == EmbeddingModel.SENTENCE_BERT:
            # Sentence transformers
            return self._embed_sentence_bert(non_empty_texts)

        elif self.model == EmbeddingModel.COHERE_ENGLISH:
            # Cohere embeddings
            return self._embed_cohere(non_empty_texts)

        return []

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Generate OpenAI embeddings."""
        try:
            response = self.client.Embedding.create(input=texts, model=self.model.value)

            embeddings = [item["embedding"] for item in response["data"]]
            logger.debug(f"Generated {len(embeddings)} OpenAI embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return [self._zero_vector() for _ in texts]

    def _embed_sentence_bert(self, texts: list[str]) -> list[list[float]]:
        """Generate sentence-BERT embeddings."""
        try:
            embeddings = self.client.encode(texts, batch_size=self.batch_size, show_progress_bar=False)

            # Convert to list of lists
            embeddings_list = [emb.tolist() for emb in embeddings]
            logger.debug(f"Generated {len(embeddings_list)} Sentence-BERT embeddings")
            return embeddings_list

        except Exception as e:
            logger.error(f"Sentence-BERT embedding failed: {e}")
            return [self._zero_vector() for _ in texts]

    def _embed_cohere(self, texts: list[str]) -> list[list[float]]:
        """Generate Cohere embeddings."""
        try:
            response = self.client.embed(texts=texts, model=self.model.value, input_type="search_document")

            embeddings = response.embeddings
            logger.debug(f"Generated {len(embeddings)} Cohere embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Cohere embedding failed: {e}")
            return [self._zero_vector() for _ in texts]

    def _zero_vector(self) -> list[float]:
        """Return zero embedding vector."""
        # Dimension based on model
        dims = {
            EmbeddingModel.OPENAI_ADA_002: 1536,
            EmbeddingModel.OPENAI_3_SMALL: 1536,
            EmbeddingModel.OPENAI_3_LARGE: 3072,
            EmbeddingModel.SENTENCE_BERT: 384,
            EmbeddingModel.COHERE_ENGLISH: 1024,
        }
        dim = dims.get(self.model, 1536)
        return [0.0] * dim

    def cosine_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
        model = EmbeddingModel(model_name)
        _embedding_service = EmbeddingService(model=model)
    return _embedding_service
