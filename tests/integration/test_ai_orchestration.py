"""
Integration tests for AI orchestration components.
"""

import pytest
from services.slm_service.app.model_router import ModelRouter, ModelProvider
from services.memory_gateway.app.vector_store import VectorStore, VectorBackend, VectorDocument
from services.memory_gateway.app.rag_pipeline import RAGPipeline
from services.memory_gateway.app.embedding_service import EmbeddingService, EmbeddingModel
from services.slm_service.app.prompt_engine import PromptEngine


class TestModelRouter:
    """Test multi-model routing."""
    
    def test_select_model_simple(self):
        """Test simple model selection."""
        router = ModelRouter()
        
        # Simple task -> efficient model
        model = router.select_model(
            prompt="What's 2+2?",
            max_cost=0.01,
            max_latency=1000
        )
        
        assert model.tier in ["efficient", "advanced"]
        assert model.cost_per_1k_tokens < 0.01
    
    def test_select_model_complex(self):
        """Test complex task routing."""
        router = ModelRouter()
        
        # Complex task -> flagship model
        complex_prompt = """
        Analyze this codebase and provide architectural recommendations.
        Consider scalability, maintainability, and performance.
        """
        
        model = router.select_model(
            prompt=complex_prompt,
            required_capabilities=["code", "reasoning"]
        )
        
        assert model.tier == "flagship"
        assert "code" in model.capabilities
    
    def test_fallback_chain(self):
        """Test fallback mechanism."""
        router = ModelRouter()
        
        # Primary fails -> fallback
        fallback = router.get_fallback("claude-3-opus")
        assert fallback is not None
        assert fallback.provider != ModelProvider.ANTHROPIC or fallback.name != "claude-3-opus"


class TestVectorStore:
    """Test vector database operations."""
    
    @pytest.mark.asyncio
    async def test_upsert_and_search(self):
        """Test document indexing and search."""
        store = VectorStore(backend=VectorBackend.CHROMADB)
        
        # Index documents
        docs = [
            VectorDocument(
                id="doc1",
                content="Python is a programming language",
                embedding=[0.1] * 1536,
                metadata={"category": "programming"}
            ),
            VectorDocument(
                id="doc2",
                content="JavaScript is used for web development",
                embedding=[0.2] * 1536,
                metadata={"category": "programming"}
            ),
        ]
        
        await store.upsert("test_collection", docs)
        
        # Search
        query_embedding = [0.15] * 1536
        results = await store.search(
            collection="test_collection",
            embedding=query_embedding,
            limit=2
        )
        
        assert len(results) == 2
        assert all(doc.score is not None for doc in results)
    
    @pytest.mark.asyncio
    async def test_collection_stats(self):
        """Test collection statistics."""
        store = VectorStore(backend=VectorBackend.CHROMADB)
        
        stats = await store.get_collection_stats("test_collection")
        assert "count" in stats


class TestRAGPipeline:
    """Test RAG pipeline."""
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self):
        """Test context retrieval."""
        pipeline = RAGPipeline(
            vector_store=VectorStore(backend=VectorBackend.CHROMADB),
            embedding_service=EmbeddingService(model=EmbeddingModel.SENTENCE_BERT)
        )
        
        # Index test data
        await pipeline.index_documents(
            user_id="test_user",
            documents=[
                {"content": "SomaAgent is an AI platform", "metadata": {}},
                {"content": "Task capsules enable reusability", "metadata": {}},
            ]
        )
        
        # Retrieve context
        context = await pipeline.retrieve_context(
            user_id="test_user",
            query="What is SomaAgent?",
            limit=2
        )
        
        assert len(context.documents) > 0
        assert context.total_tokens > 0
    
    def test_augment_prompt(self):
        """Test prompt augmentation."""
        pipeline = RAGPipeline(
            vector_store=VectorStore(backend=VectorBackend.CHROMADB),
            embedding_service=EmbeddingService()
        )
        
        documents = [
            {"content": "Context information", "score": 0.9, "metadata": {}}
        ]
        
        augmented = pipeline.augment_prompt(
            original_prompt="What is this?",
            documents=documents
        )
        
        assert "Context information" in augmented
        assert "What is this?" in augmented


class TestEmbeddingService:
    """Test embedding generation."""
    
    def test_embed_text(self):
        """Test single text embedding."""
        service = EmbeddingService(model=EmbeddingModel.SENTENCE_BERT)
        
        embedding = service.embed_text("Hello world")
        
        assert len(embedding) == 384  # Sentence-BERT dimension
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_batch(self):
        """Test batch embedding."""
        service = EmbeddingService(model=EmbeddingModel.SENTENCE_BERT)
        
        texts = ["First text", "Second text", "Third text"]
        embeddings = service.embed_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_cosine_similarity(self):
        """Test similarity calculation."""
        service = EmbeddingService(model=EmbeddingModel.SENTENCE_BERT)
        
        emb1 = service.embed_text("Hello world")
        emb2 = service.embed_text("Hello world")
        emb3 = service.embed_text("Goodbye universe")
        
        # Same text should be very similar
        sim_same = service.cosine_similarity(emb1, emb2)
        assert sim_same > 0.99
        
        # Different text should be less similar
        sim_diff = service.cosine_similarity(emb1, emb3)
        assert sim_diff < 0.99


class TestPromptEngine:
    """Test prompt template engine."""
    
    def test_render_system_prompt(self):
        """Test system prompt rendering."""
        engine = PromptEngine()
        
        rendered = engine.render(
            "sys_coding_assistant",
            {"languages": "Python, JavaScript, Go"}
        )
        
        assert "Python" in rendered
        assert "JavaScript" in rendered
        assert "expert software engineer" in rendered
    
    def test_render_rag_prompt(self):
        """Test RAG prompt rendering."""
        engine = PromptEngine()
        
        rendered = engine.render(
            "user_rag_context",
            {
                "documents": [
                    {"content": "Doc 1 content"},
                    {"content": "Doc 2 content"}
                ],
                "question": "What is the answer?"
            }
        )
        
        assert "Doc 1 content" in rendered
        assert "Doc 2 content" in rendered
        assert "What is the answer?" in rendered
    
    def test_create_chain(self):
        """Test message chain creation."""
        engine = PromptEngine()
        
        messages = engine.create_chain(
            templates=["sys_default_assistant", "user_rag_context"],
            variables={
                "documents": [{"content": "Context"}],
                "question": "Question?"
            }
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_list_templates(self):
        """Test template listing."""
        engine = PromptEngine()
        
        # List all templates
        all_templates = engine.list_templates()
        assert len(all_templates) > 0
        
        # Filter by category
        system_templates = engine.list_templates(category="system")
        assert all(t.category == "system" for t in system_templates)
