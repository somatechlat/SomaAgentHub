"""
⚠️ WE DO NOT MOCK - Load tests hit REAL services with actual workloads.

Locust Performance Testing Scenarios
Tests MAO throughput, tool invocation latency, concurrent project creation.
Target: P95 < 200ms for tool invocations
"""

from locust import HttpUser, task, between, events
import json
import time
from datetime import datetime
import random


class ToolRegistryLoadTest(HttpUser):
    """Load test for Tool Registry service."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup - authenticate and get session token."""
        response = self.client.post("/v1/session/mint", json={
            "tenant": "load-test-tenant",
            "persona_hash": "sha256-test",
            "policy_hash": "sha256-test",
            "budgets": {
                "tokens": 1000000,
                "tools_per_min": 600
            }
        })
        self.token = response.json().get("jwt")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def list_tools(self):
        """Test listing available tools."""
        with self.client.get("/v1/tools", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                tools = response.json()
                if len(tools) >= 10:
                    response.success()
                else:
                    response.failure(f"Expected >= 10 tools, got {len(tools)}")
    
    @task(30)
    def get_tool_capabilities(self):
        """Test getting tool capabilities (high frequency)."""
        tools = ["github", "slack", "jira", "plane", "aws", "kubernetes"]
        tool = random.choice(tools)
        
        start_time = time.time()
        with self.client.get(f"/v1/tools/{tool}/capabilities",
                           headers=self.headers,
                           catch_response=True) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if latency_ms < 200:  # P95 target
                    response.success()
                else:
                    response.failure(f"Latency {latency_ms:.2f}ms exceeds 200ms target")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(15)
    def invoke_tool(self):
        """Test tool invocation."""
        # Test lightweight operations
        operations = [
            ("github", "get_authenticated_user", {}),
            ("slack", "list_channels", {}),
            ("jira", "get_myself", {}),
        ]
        
        tool, capability, params = random.choice(operations)
        
        start_time = time.time()
        with self.client.post(f"/v1/tools/{tool}/invoke",
                            json={
                                "capability": capability,
                                "parameters": params
                            },
                            headers=self.headers,
                            catch_response=True) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if latency_ms < 200:
                    response.success()
                else:
                    response.failure(f"Tool invocation {latency_ms:.2f}ms > 200ms")
    
    @task(5)
    def health_check_tool(self):
        """Test tool health checks."""
        tools = ["github", "slack", "aws"]
        tool = random.choice(tools)
        
        with self.client.get(f"/v1/tools/{tool}/health",
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                health = response.json()
                if health.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Tool {tool} unhealthy: {health}")


class MAOLoadTest(HttpUser):
    """Load test for Multi-Agent Orchestrator."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup session."""
        response = self.client.post("/v1/session/mint", json={
            "tenant": "mao-load-test",
            "budgets": {"tokens": 5000000}
        })
        self.token = response.json().get("jwt")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(20)
    def create_simple_workflow(self):
        """Test creating simple workflow (sequential)."""
        workflow = {
            "type": "sequential",
            "tasks": [
                {
                    "id": "task1",
                    "tool": "github",
                    "capability": "get_authenticated_user",
                    "parameters": {}
                },
                {
                    "id": "task2",
                    "tool": "slack",
                    "capability": "list_channels",
                    "parameters": {}
                }
            ]
        }
        
        start_time = time.time()
        with self.client.post("/v1/workflows/execute",
                            json=workflow,
                            headers=self.headers,
                            catch_response=True) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "completed":
                    response.success()
                else:
                    response.failure(f"Workflow failed: {result.get('error')}")
    
    @task(10)
    def create_parallel_workflow(self):
        """Test parallel workflow execution."""
        workflow = {
            "type": "parallel",
            "tasks": [
                {
                    "id": "github_task",
                    "tool": "github",
                    "capability": "get_authenticated_user",
                    "parameters": {}
                },
                {
                    "id": "slack_task",
                    "tool": "slack",
                    "capability": "list_channels",
                    "parameters": {}
                },
                {
                    "id": "jira_task",
                    "tool": "jira",
                    "capability": "get_myself",
                    "parameters": {}
                }
            ]
        }
        
        start_time = time.time()
        with self.client.post("/v1/workflows/execute",
                            json=workflow,
                            headers=self.headers,
                            catch_response=True) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Parallel should be faster than sequential
                if latency_ms < 500:  # 3 tasks in parallel should be < 500ms
                    response.success()
                else:
                    response.failure(f"Parallel workflow too slow: {latency_ms:.2f}ms")
    
    @task(5)
    def create_dag_workflow(self):
        """Test DAG workflow execution."""
        workflow = {
            "type": "dag",
            "tasks": [
                {
                    "id": "setup",
                    "tool": "github",
                    "capability": "get_authenticated_user",
                    "parameters": {},
                    "dependencies": []
                },
                {
                    "id": "parallel_1",
                    "tool": "slack",
                    "capability": "list_channels",
                    "parameters": {},
                    "dependencies": ["setup"]
                },
                {
                    "id": "parallel_2",
                    "tool": "jira",
                    "capability": "get_myself",
                    "parameters": {},
                    "dependencies": ["setup"]
                },
                {
                    "id": "finalize",
                    "tool": "github",
                    "capability": "get_rate_limit",
                    "parameters": {},
                    "dependencies": ["parallel_1", "parallel_2"]
                }
            ]
        }
        
        with self.client.post("/v1/workflows/execute",
                            json=workflow,
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "completed":
                    response.success()


class KAMACHIQLoadTest(HttpUser):
    """Load test for KAMACHIQ conversational console."""
    
    wait_time = between(3, 7)
    
    def on_start(self):
        """Initialize session."""
        self.session_id = f"load-test-{int(time.time())}-{random.randint(1000, 9999)}"
    
    @task(15)
    def simple_query(self):
        """Test simple conversational queries."""
        queries = [
            "What tools are available?",
            "Show me the status of my projects",
            "List all GitHub repositories",
            "What are the available project templates?"
        ]
        
        query = random.choice(queries)
        
        start_time = time.time()
        with self.client.post("/v1/kamachiq/chat",
                            json={
                                "session_id": self.session_id,
                                "message": query
                            },
                            catch_response=True) as response:
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if latency_ms < 1000:  # Conversational queries should be fast
                    response.success()
                else:
                    response.failure(f"Response too slow: {latency_ms:.2f}ms")
    
    @task(5)
    def project_creation_intent(self):
        """Test project creation intent parsing."""
        prompts = [
            "Create a web app called TestApp with React and Python",
            "I need an API service for user management",
            "Build a mobile app for iOS and Android"
        ]
        
        prompt = random.choice(prompts)
        
        with self.client.post("/v1/kamachiq/parse-intent",
                            json={"message": prompt},
                            catch_response=True) as response:
            if response.status_code == 200:
                intent = response.json()
                if intent.get("project_type"):
                    response.success()
                else:
                    response.failure("Failed to parse project intent")


# ============================================================================
# CUSTOM METRICS
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize custom metrics tracking."""
    print("\n" + "="*60)
    print("Starting SomaGent Performance Load Tests")
    print(f"Test started at: {datetime.utcnow().isoformat()}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary metrics."""
    print("\n" + "="*60)
    print("Load Test Summary")
    print("="*60)
    
    stats = environment.stats
    
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Failure rate: {(stats.total.num_failures / stats.total.num_requests * 100) if stats.total.num_requests > 0 else 0:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"P95 response time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99 response time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    
    # Check if P95 meets target
    p95 = stats.total.get_response_time_percentile(0.95)
    if p95 < 200:
        print(f"\n✓ SUCCESS: P95 latency {p95:.2f}ms meets < 200ms target")
    else:
        print(f"\n✗ WARNING: P95 latency {p95:.2f}ms exceeds 200ms target")
    
    print("\n" + "="*60 + "\n")
