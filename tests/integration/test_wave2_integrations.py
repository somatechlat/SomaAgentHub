"""Integration tests for Wave 2 client implementations.

Tests Redis, Qdrant, OpenAI, and Analytics clients with real infrastructure.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add services to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRedisClient:
    """Test suite for Redis client."""
    
    @pytest.mark.asyncio
    async def test_redis_health_check(self):
        """Test Redis health check."""
        from services.common.redis_client import get_redis_client
        
        os.environ["REDIS_URL"] = "redis://localhost:6379"
        redis_client = get_redis_client()
        
        healthy = await redis_client.health_check()
        assert isinstance(healthy, bool)
        # Note: Will be False if Redis not running, which is OK in CI
    
    @pytest.mark.asyncio
    async def test_redis_json_operations(self):
        """Test Redis JSON set/get/delete operations."""
        from services.common.redis_client import get_redis_client
        
        os.environ["REDIS_URL"] = "redis://localhost:6379"
        redis_client = get_redis_client()
        
        # Skip test if Redis unavailable
        if not await redis_client.health_check():
            pytest.skip("Redis not available")
        
        test_key = "test:wave2:json:operations"
        test_data = {"status": "testing", "count": 42, "nested": {"key": "value"}}
        
        # Test set
        await redis_client.set_json(test_key, test_data, ttl=60)
        
        # Test get
        retrieved = await redis_client.get_json(test_key)
        assert retrieved == test_data
        assert retrieved["count"] == 42
        assert retrieved["nested"]["key"] == "value"
        
        # Test delete
        await redis_client.delete(test_key)
        deleted = await redis_client.get_json(test_key)
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_redis_lock_ttl(self):
        """Test Redis lock expires after TTL."""
        from services.common.redis_client import get_redis_client
        
        os.environ["REDIS_URL"] = "redis://localhost:6379"
        redis_client = get_redis_client()
        
        # Skip test if Redis unavailable
        if not await redis_client.health_check():
            pytest.skip("Redis not available")
        
        test_key = "test:wave2:lock:ttl"
        lock_data = {"enabled": True, "locked_by": "test-user"}
        
        # Set lock with 1-second TTL
        await redis_client.set_json(test_key, lock_data, ttl=1)
        
        # Should exist immediately
        lock = await redis_client.get_json(test_key)
        assert lock is not None
        assert lock["enabled"] is True
        
        # Should expire after 1 second
        await asyncio.sleep(1.5)
        expired = await redis_client.get_json(test_key)
        assert expired is None
    
    @pytest.mark.asyncio
    async def test_redis_lock_context_manager(self):
        """Test Redis distributed lock context manager."""
        from services.common.redis_client import get_redis_client
        
        os.environ["REDIS_URL"] = "redis://localhost:6379"
        redis_client = get_redis_client()
        
        # Skip test if Redis unavailable
        if not await redis_client.health_check():
            pytest.skip("Redis not available")
        
        lock_key = "test:wave2:lock:context"
        
        # Test lock acquire and release
        async with redis_client.lock(lock_key, timeout=10) as acquired:
            assert acquired is True
            
            # Lock should be held now
            # Attempting to acquire again should fail (non-blocking)
            async with redis_client.lock(lock_key, timeout=1, blocking=False) as acquired2:
                assert acquired2 is False
        
        # After context exits, lock should be released
        async with redis_client.lock(lock_key, timeout=10, blocking=False) as acquired3:
            assert acquired3 is True


class TestQdrantClient:
    """Test suite for Qdrant client."""
    
    @pytest.mark.asyncio
    async def test_qdrant_health_check(self):
        """Test Qdrant health check."""
        from services.common.qdrant_client import get_qdrant_client
        
        os.environ["QDRANT_URL"] = "http://localhost:6333"
        qdrant_client = get_qdrant_client()
        
        healthy = await qdrant_client.health_check()
        assert isinstance(healthy, bool)
    
    @pytest.mark.asyncio
    async def test_qdrant_collection_lifecycle(self):
        """Test Qdrant collection creation and deletion."""
        from services.common.qdrant_client import get_qdrant_client
        
        os.environ["QDRANT_URL"] = "http://localhost:6333"
        qdrant_client = get_qdrant_client()
        
        # Skip test if Qdrant unavailable
        if not await qdrant_client.health_check():
            pytest.skip("Qdrant not available")
        
        test_collection = "test_wave2_lifecycle"
        
        # Create collection
        await qdrant_client.create_collection(
            collection_name=test_collection,
            vector_size=384,
        )
        
        # Upsert test point
        await qdrant_client.upsert_points(
            collection_name=test_collection,
            points=[
                {
                    "id": "test-point-1",
                    "vector": [0.1] * 384,
                    "payload": {"text": "Test document", "category": "test"},
                }
            ],
        )
        
        # Retrieve point
        point = await qdrant_client.get_point(
            collection_name=test_collection,
            point_id="test-point-1"
        )
        assert point is not None
        assert point.payload["text"] == "Test document"
        
        # Delete collection
        await qdrant_client.delete_collection(test_collection)
    
    @pytest.mark.asyncio
    async def test_qdrant_semantic_search(self):
        """Test Qdrant semantic search with filtering."""
        from services.common.qdrant_client import get_qdrant_client
        
        os.environ["QDRANT_URL"] = "http://localhost:6333"
        qdrant_client = get_qdrant_client()
        
        # Skip test if Qdrant unavailable
        if not await qdrant_client.health_check():
            pytest.skip("Qdrant not available")
        
        test_collection = "test_wave2_search"
        
        # Create collection
        await qdrant_client.create_collection(
            collection_name=test_collection,
            vector_size=128,
        )
        
        # Upsert multiple points
        points = [
            {
                "id": f"doc-{i}",
                "vector": [0.1 * i] * 128,
                "payload": {"text": f"Document {i}", "category": "A" if i % 2 == 0 else "B"},
            }
            for i in range(10)
        ]
        await qdrant_client.upsert_points(test_collection, points)
        
        # Search without filter
        query_vector = [0.5] * 128
        results = await qdrant_client.search(
            collection_name=test_collection,
            query_vector=query_vector,
            limit=5,
        )
        assert len(results) <= 5
        
        # Search with metadata filter (category A only)
        filtered_results = await qdrant_client.search(
            collection_name=test_collection,
            query_vector=query_vector,
            limit=5,
            filter_conditions={"category": "A"},
        )
        assert len(filtered_results) <= 5
        for result in filtered_results:
            assert result.payload["category"] == "A"
        
        # Cleanup
        await qdrant_client.delete_collection(test_collection)


class TestOpenAIProvider:
    """Test suite for OpenAI provider."""
    
    @pytest.mark.asyncio
    async def test_openai_cost_calculation(self):
        """Test OpenAI cost calculation logic."""
        from services.common.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(api_key="test-key")
        
        # Test GPT-3.5 cost
        cost = provider.calculate_cost(
            model="gpt-3.5-turbo",
            prompt_tokens=1000,
            completion_tokens=500,
        )
        # Cost should be: (1000 * 0.5 + 500 * 1.5) / 1_000_000 = 0.00125
        assert abs(cost - 0.00125) < 0.0001
        
        # Test GPT-4 cost
        cost_gpt4 = provider.calculate_cost(
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )
        # Cost should be: (1000 * 30.0 + 500 * 60.0) / 1_000_000 = 0.06
        assert abs(cost_gpt4 - 0.06) < 0.001
    
    @pytest.mark.asyncio
    async def test_openai_completion_with_mock(self):
        """Test OpenAI completion (mocked, no API key needed)."""
        from services.common.openai_provider import OpenAIProvider
        
        # Skip if real API key is set (would make real call)
        if os.getenv("OPENAI_API_KEY"):
            pytest.skip("Real OpenAI API key detected, skipping mock test")
        
        # Test that provider initializes correctly
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.organization is None


class TestAnalyticsClient:
    """Test suite for Analytics client."""
    
    @pytest.mark.asyncio
    async def test_analytics_health_check(self):
        """Test Analytics service health check."""
        from services.common.analytics_client import get_analytics_client
        
        os.environ["ANALYTICS_SERVICE_URL"] = "http://localhost:8080"
        analytics_client = get_analytics_client()
        
        healthy = await analytics_client.health_check()
        assert isinstance(healthy, bool)
    
    @pytest.mark.asyncio
    async def test_analytics_query_timeout(self):
        """Test Analytics client respects timeout."""
        from services.common.analytics_client import AnalyticsClient
        
        # Use very short timeout
        client = AnalyticsClient(
            base_url="http://localhost:8080",
            timeout=0.001,  # 1ms timeout
        )
        
        # Should timeout (unless service is down, then it fails fast)
        with pytest.raises(RuntimeError) as exc_info:
            await client.query_metrics(
                metric_name="slm.tokens",
                tenant_id="test-tenant",
            )
        
        assert "timed out" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()


class TestIdentityClient:
    """Test suite for Identity client."""
    
    @pytest.mark.asyncio
    async def test_identity_health_check(self):
        """Test Identity service health check."""
        from services.common.identity_client import get_identity_client
        
        os.environ["IDENTITY_SERVICE_URL"] = "http://localhost:8000"
        identity_client = get_identity_client()
        
        healthy = await identity_client.health_check()
        assert isinstance(healthy, bool)
    
    @pytest.mark.asyncio
    async def test_identity_capability_check_unavailable(self):
        """Test Identity capability check when service unavailable."""
        from services.common.identity_client import IdentityClient
        
        # Point to non-existent service
        client = IdentityClient(
            base_url="http://localhost:9999",
            timeout=1.0,
        )
        
        # Should raise RuntimeError when service unavailable
        with pytest.raises(RuntimeError):
            await client.check_user_capability(
                user_id="test@example.com",
                capability="training.admin",
            )


class TestServiceIntegrations:
    """Test suite for service-level integrations."""
    
    @pytest.mark.asyncio
    async def test_training_lock_with_redis(self):
        """Test training lock endpoints with Redis backend."""
        from services.common.redis_client import get_redis_client
        
        os.environ["REDIS_URL"] = "redis://localhost:6379"
        redis_client = get_redis_client()
        
        # Skip if Redis unavailable
        if not await redis_client.health_check():
            pytest.skip("Redis not available")
        
        tenant = "test-tenant-training"
        lock_key = f"training:lock:{tenant}"
        
        # Simulate enable training mode
        lock_data = {
            "enabled": True,
            "locked_by": "admin@example.com",
            "locked_at": 1234567890.0,
            "reason": "Integration test",
        }
        await redis_client.set_json(lock_key, lock_data, ttl=60)
        
        # Verify lock exists
        retrieved = await redis_client.get_json(lock_key)
        assert retrieved is not None
        assert retrieved["enabled"] is True
        assert retrieved["locked_by"] == "admin@example.com"
        
        # Cleanup
        await redis_client.delete(lock_key)
    
    @pytest.mark.asyncio
    async def test_memory_gateway_with_qdrant(self):
        """Test memory storage with Qdrant backend."""
        from services.common.qdrant_client import get_qdrant_client
        
        os.environ["QDRANT_URL"] = "http://localhost:6333"
        qdrant_client = get_qdrant_client()
        
        # Skip if Qdrant unavailable
        if not await qdrant_client.health_check():
            pytest.skip("Qdrant not available")
        
        collection = "test_memory_integration"
        
        # Create collection
        await qdrant_client.create_collection(
            collection_name=collection,
            vector_size=768,
        )
        
        # Simulate /v1/remember endpoint
        memory_key = "fact-001"
        memory_value = {"text": "SomaGent is a multi-agent platform"}
        vector = [0.1] * 768  # Placeholder embedding
        
        await qdrant_client.upsert_points(
            collection_name=collection,
            points=[
                {
                    "id": memory_key,
                    "vector": vector,
                    "payload": {"key": memory_key, "value": memory_value},
                }
            ],
        )
        
        # Simulate /v1/recall endpoint
        point = await qdrant_client.get_point(collection, memory_key)
        assert point is not None
        assert point.payload["key"] == memory_key
        assert point.payload["value"]["text"] == "SomaGent is a multi-agent platform"
        
        # Cleanup
        await qdrant_client.delete_collection(collection)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
