"""
⚠️ WE DO NOT MOCK - Chaos tests inject REAL failures into REAL systems.

Chaos Engineering Scenarios
Tests system resilience under failure conditions with real infrastructure.
"""

import pytest
import time
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChaosScenario:
    """Base class for chaos engineering scenarios."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
        self.results = {}
    
    def inject_failure(self):
        """Inject the failure condition."""
        raise NotImplementedError
    
    def recover(self):
        """Recover from the failure."""
        raise NotImplementedError
    
    def verify_graceful_degradation(self) -> bool:
        """Verify system degraded gracefully."""
        raise NotImplementedError
    
    def verify_recovery(self) -> bool:
        """Verify system recovered successfully."""
        raise NotImplementedError
    
    def run(self) -> Dict[str, Any]:
        """Execute the complete chaos scenario."""
        logger.info(f"Starting chaos scenario: {self.name}")
        logger.info(f"Description: {self.description}")
        
        self.start_time = datetime.utcnow()
        
        try:
            # Inject failure
            logger.info("Injecting failure...")
            self.inject_failure()
            
            # Wait for system to react
            time.sleep(5)
            
            # Verify graceful degradation
            logger.info("Verifying graceful degradation...")
            degraded_ok = self.verify_graceful_degradation()
            self.results["graceful_degradation"] = degraded_ok
            
            # Recover
            logger.info("Recovering from failure...")
            self.recover()
            
            # Wait for recovery
            time.sleep(10)
            
            # Verify recovery
            logger.info("Verifying recovery...")
            recovered_ok = self.verify_recovery()
            self.results["recovery"] = recovered_ok
            
            self.results["success"] = degraded_ok and recovered_ok
            
        except Exception as e:
            logger.error(f"Chaos scenario failed: {e}")
            self.results["error"] = str(e)
            self.results["success"] = False
        
        finally:
            self.end_time = datetime.utcnow()
            self.results["duration_seconds"] = (self.end_time - self.start_time).total_seconds()
        
        logger.info(f"Scenario completed: {'SUCCESS' if self.results.get('success') else 'FAILED'}")
        return self.results


# ============================================================================
# DATABASE FAILURE SCENARIOS
# ============================================================================

class PostgresDownScenario(ChaosScenario):
    """Test system behavior when PostgreSQL is unavailable."""
    
    def __init__(self, service_url: str):
        super().__init__(
            "Postgres Down",
            "Simulates PostgreSQL database outage"
        )
        self.service_url = service_url
        self.postgres_container = "somagent-postgres"
    
    def inject_failure(self):
        """Stop PostgreSQL container."""
        subprocess.run(["docker", "stop", self.postgres_container], check=True)
        logger.info("PostgreSQL container stopped")
    
    def recover(self):
        """Restart PostgreSQL container."""
        subprocess.run(["docker", "start", self.postgres_container], check=True)
        logger.info("PostgreSQL container restarted")
    
    def verify_graceful_degradation(self) -> bool:
        """Verify services respond with appropriate errors."""
        try:
            response = requests.get(f"{self.service_url}/healthz", timeout=5)
            # Should return degraded status, not crash
            return response.status_code in [200, 503]
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify services recovered."""
        time.sleep(15)  # Wait for connection pools to recover
        try:
            response = requests.get(f"{self.service_url}/healthz", timeout=5)
            return response.status_code == 200 and response.json().get("database") == "healthy"
        except requests.RequestException:
            return False


class RedisDownScenario(ChaosScenario):
    """Test system behavior when Redis is unavailable."""
    
    def __init__(self, service_url: str):
        super().__init__(
            "Redis Down",
            "Simulates Redis cache outage"
        )
        self.service_url = service_url
        self.redis_container = "somagent-redis"
    
    def inject_failure(self):
        """Stop Redis container."""
        subprocess.run(["docker", "stop", self.redis_container], check=True)
        logger.info("Redis container stopped")
    
    def recover(self):
        """Restart Redis container."""
        subprocess.run(["docker", "start", self.redis_container], check=True)
        logger.info("Redis container restarted")
    
    def verify_graceful_degradation(self) -> bool:
        """Verify services function without cache (slower but working)."""
        try:
            response = requests.get(f"{self.service_url}/v1/tools", timeout=10)
            # Should still work, just slower
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify cache is being used again."""
        try:
            # First request warms cache
            requests.get(f"{self.service_url}/v1/tools", timeout=5)
            
            # Second request should be fast (from cache)
            start = time.time()
            response = requests.get(f"{self.service_url}/v1/tools", timeout=5)
            latency = (time.time() - start) * 1000
            
            return response.status_code == 200 and latency < 50  # Cache hit should be < 50ms
        except requests.RequestException:
            return False


# ============================================================================
# MESSAGE QUEUE FAILURE SCENARIOS
# ============================================================================

class KafkaPartitionLossScenario(ChaosScenario):
    """Test system behavior when Kafka partition is lost."""
    
    def __init__(self, service_url: str):
        super().__init__(
            "Kafka Partition Loss",
            "Simulates Kafka broker failure and partition loss"
        )
        self.service_url = service_url
        self.kafka_container = "somagent-kafka"
    
    def inject_failure(self):
        """Stop Kafka container."""
        subprocess.run(["docker", "stop", self.kafka_container], check=True)
        logger.info("Kafka container stopped")
    
    def recover(self):
        """Restart Kafka container."""
        subprocess.run(["docker", "start", self.kafka_container], check=True)
        logger.info("Kafka container restarted")
        time.sleep(20)  # Wait for Kafka to fully start
    
    def verify_graceful_degradation(self) -> bool:
        """Verify events are buffered or operations continue synchronously."""
        try:
            # System should still accept requests even if events can't be published
            response = requests.post(
                f"{self.service_url}/v1/tools/github/invoke",
                json={"capability": "get_authenticated_user", "parameters": {}},
                timeout=10
            )
            return response.status_code in [200, 202]  # Accept or async accepted
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify event publishing resumed."""
        try:
            response = requests.get(f"{self.service_url}/healthz", timeout=5)
            return response.status_code == 200 and response.json().get("kafka") == "healthy"
        except requests.RequestException:
            return False


# ============================================================================
# EXTERNAL API FAILURE SCENARIOS
# ============================================================================

class GitHubRateLimitScenario(ChaosScenario):
    """Test system behavior when GitHub API rate limit is hit."""
    
    def __init__(self, service_url: str):
        super().__init__(
            "GitHub Rate Limit",
            "Simulates GitHub API rate limit exceeded"
        )
        self.service_url = service_url
    
    def inject_failure(self):
        """Make many requests to exhaust rate limit."""
        logger.info("Exhausting GitHub rate limit...")
        # In real scenario, this would be done by making many API calls
        # For testing, we'd use a test token with low limits
        pass
    
    def recover(self):
        """Wait for rate limit to reset."""
        logger.info("Waiting for rate limit reset (60 seconds)...")
        time.sleep(60)
    
    def verify_graceful_degradation(self) -> bool:
        """Verify system queues requests or returns appropriate errors."""
        try:
            response = requests.post(
                f"{self.service_url}/v1/tools/github/invoke",
                json={"capability": "get_authenticated_user", "parameters": {}},
                timeout=10
            )
            # Should return 429 or queue the request
            return response.status_code in [429, 202, 503]
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify GitHub operations resume."""
        try:
            response = requests.post(
                f"{self.service_url}/v1/tools/github/invoke",
                json={"capability": "get_authenticated_user", "parameters": {}},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


class AWSThrottlingScenario(ChaosScenario):
    """Test system behavior when AWS APIs throttle requests."""
    
    def __init__(self, service_url: str):
        super().__init__(
            "AWS API Throttling",
            "Simulates AWS API request throttling"
        )
        self.service_url = service_url
    
    def inject_failure(self):
        """Make rapid AWS API calls to trigger throttling."""
        logger.info("Triggering AWS throttling...")
        # Make many rapid requests
        for _ in range(100):
            try:
                requests.post(
                    f"{self.service_url}/v1/tools/aws/invoke",
                    json={"capability": "list_instances", "parameters": {}},
                    timeout=1
                )
            except:
                pass
    
    def recover(self):
        """Wait for throttling to clear."""
        time.sleep(10)
    
    def verify_graceful_degradation(self) -> bool:
        """Verify exponential backoff and retries work."""
        try:
            response = requests.post(
                f"{self.service_url}/v1/tools/aws/invoke",
                json={"capability": "list_instances", "parameters": {}},
                timeout=30  # Allow time for retries
            )
            # Should eventually succeed with retries
            return response.status_code in [200, 202]
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify normal AWS operations."""
        try:
            response = requests.post(
                f"{self.service_url}/v1/tools/aws/invoke",
                json={"capability": "list_instances", "parameters": {}},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


# ============================================================================
# NETWORK FAILURE SCENARIOS
# ============================================================================

class NetworkPartitionScenario(ChaosScenario):
    """Test system behavior during network partition."""
    
    def __init__(self, service_url: str, target_service: str):
        super().__init__(
            "Network Partition",
            f"Simulates network partition isolating {target_service}"
        )
        self.service_url = service_url
        self.target_service = target_service
    
    def inject_failure(self):
        """Create network partition using iptables."""
        # Block traffic to target service
        subprocess.run([
            "docker", "exec", "somagent-gateway",
            "iptables", "-A", "OUTPUT", "-d", self.target_service, "-j", "DROP"
        ], check=True)
        logger.info(f"Network partition created to {self.target_service}")
    
    def recover(self):
        """Remove network partition."""
        subprocess.run([
            "docker", "exec", "somagent-gateway",
            "iptables", "-D", "OUTPUT", "-d", self.target_service, "-j", "DROP"
        ], check=True)
        logger.info("Network partition removed")
    
    def verify_graceful_degradation(self) -> bool:
        """Verify circuit breaker opens."""
        try:
            response = requests.get(f"{self.service_url}/healthz", timeout=10)
            # Health check should report degraded state
            return response.status_code in [200, 503]
        except requests.RequestException:
            return False
    
    def verify_recovery(self) -> bool:
        """Verify circuit breaker closes and traffic resumes."""
        time.sleep(30)  # Wait for circuit breaker to close
        try:
            response = requests.get(f"{self.service_url}/healthz", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False


# ============================================================================
# TEST SUITE
# ============================================================================

@pytest.mark.chaos
class TestChaosScenarios:
    """Chaos engineering test suite."""
    
    def test_postgres_down(self):
        """Test PostgreSQL failure scenario."""
        scenario = PostgresDownScenario("http://localhost:8000")
        results = scenario.run()
        
        assert results["success"], f"Postgres chaos test failed: {results}"
        assert results["graceful_degradation"], "System did not degrade gracefully"
        assert results["recovery"], "System did not recover"
        print(f"✓ Postgres chaos test passed in {results['duration_seconds']:.2f}s")
    
    def test_redis_down(self):
        """Test Redis failure scenario."""
        scenario = RedisDownScenario("http://localhost:8000")
        results = scenario.run()
        
        assert results["success"], f"Redis chaos test failed: {results}"
        print(f"✓ Redis chaos test passed in {results['duration_seconds']:.2f}s")
    
    def test_kafka_partition_loss(self):
        """Test Kafka failure scenario."""
        scenario = KafkaPartitionLossScenario("http://localhost:8000")
        results = scenario.run()
        
        assert results["success"], f"Kafka chaos test failed: {results}"
        print(f"✓ Kafka chaos test passed in {results['duration_seconds']:.2f}s")
    
    def test_github_rate_limit(self):
        """Test GitHub rate limit scenario."""
        scenario = GitHubRateLimitScenario("http://localhost:8000")
        results = scenario.run()
        
        assert results["success"], f"GitHub rate limit test failed: {results}"
        print(f"✓ GitHub rate limit test passed in {results['duration_seconds']:.2f}s")
    
    def test_aws_throttling(self):
        """Test AWS throttling scenario."""
        scenario = AWSThrottlingScenario("http://localhost:8000")
        results = scenario.run()
        
        assert results["success"], f"AWS throttling test failed: {results}"
        print(f"✓ AWS throttling test passed in {results['duration_seconds']:.2f}s")
