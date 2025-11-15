# SomaAgent01 - Basic Agent Setup

![Version](https://img.shields.io/badge/version-1.0.0-blue)

**Your first autonomous agent integration with SomaAgentHub**

> Complete guide for creating your first AI agent that can authenticate, communicate, and execute tasks within the SomaAgentHub ecosystem.

---

## 📋 Overview

SomaAgent01 is the foundational pattern for any autonomous agent integrating with SomaAgentHub. This guide walks through creating a minimal but complete agent that can:

- **Authenticate** with the identity service
- **Create sessions** for stateful interactions
- **Execute tasks** through the orchestrator
- **Handle errors** gracefully with retries
- **Monitor health** and report status

---

## 🎯 Learning Objectives

By completing this guide, your SomaAgent01 will:

✅ **Authenticate** using service account tokens  
✅ **Create and manage** agent sessions  
✅ **Execute basic tasks** through the orchestrator  
✅ **Handle common errors** with proper retry logic  
✅ **Implement health checks** for monitoring  
✅ **Follow security best practices** for production use  

---

## 🚀 Quick Start (15 Minutes)

### Prerequisites

**System Requirements:**
- Python 3.11+ or Node.js 18+
- Network access to SomaAgentHub services
- Basic understanding of REST APIs

**SomaAgentHub Services Running:**
```bash
# Verify services are accessible
curl -f http://localhost:10000/healthz  # Gateway API
curl -f http://localhost:10001/ready    # Orchestrator
curl -f http://localhost:10002/health   # Identity Service
```

### Step 1: Agent Authentication

**Create Service Account:**
```python
import requests
import json
from datetime import datetime, timedelta

class SomaAgent01:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.base_url = "http://localhost"
        self.token = None
        self.token_expires = None
        
    def authenticate(self) -> bool:
        """Authenticate with identity service"""
        try:
            response = requests.post(
                f"{self.base_url}:10002/v1/tokens/service",
                json={
                    "service_name": self.agent_name,
                    "scopes": ["agent:execute", "session:create", "memory:read"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
                print(f"✅ Authentication successful for {self.agent_name}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_auth_headers(self) -> dict:
        """Get authentication headers for requests"""
        if not self.token or datetime.now() >= self.token_expires:
            if not self.authenticate():
                raise Exception("Failed to authenticate")
        
        return {"Authorization": f"Bearer {self.token}"}

# Initialize your agent
agent = SomaAgent01("my-first-agent")
success = agent.authenticate()
```

### Step 2: Create Agent Session

**Session Management:**
```python
def create_session(self) -> str:
    """Create a new agent session"""
    try:
        response = requests.post(
            f"{self.base_url}:10000/v1/sessions",
            headers=self.get_auth_headers(),
            json={
                "agent_type": "automation",
                "session_config": {
                    "timeout_seconds": 300,
                    "memory_enabled": True,
                    "tools_enabled": ["web_search", "file_operations"],
                    "max_iterations": 10
                }
            },
            timeout=30
        )
        
        if response.status_code == 201:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
            return session_id
        else:
            print(f"❌ Session creation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return None

# Add to SomaAgent01 class
SomaAgent01.create_session = create_session

# Create a session
session_id = agent.create_session()
```

### Step 3: Execute Your First Task

**Task Execution:**
```python
def execute_task(self, session_id: str, task_description: str) -> dict:
    """Execute a task through the orchestrator"""
    try:
        response = requests.post(
            f"{self.base_url}:10001/v1/workflows/execute",
            headers=self.get_auth_headers(),
            json={
                "workflow_type": "agent_task",
                "session_id": session_id,
                "task": {
                    "type": "general",
                    "description": task_description,
                    "priority": "normal",
                    "timeout_seconds": 120
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Task executed successfully")
            print(f"   Workflow ID: {result.get('workflow_id')}")
            print(f"   Status: {result.get('status')}")
            return result
        else:
            print(f"❌ Task execution failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Task execution error: {e}")
        return None

# Add to SomaAgent01 class
SomaAgent01.execute_task = execute_task

# Execute a simple task
result = agent.execute_task(session_id, "Check system health and report status")
```

### Step 4: Complete SomaAgent01 Implementation

**Full Agent Implementation:**
```python
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class SomaAgent01:
    """
    Basic autonomous agent for SomaAgentHub integration
    
    Features:
    - Service account authentication with auto-refresh
    - Session management with proper cleanup
    - Task execution with error handling
    - Health monitoring and status reporting
    """
    
    def __init__(self, agent_name: str, base_url: str = "http://localhost"):
        self.agent_name = agent_name
        self.base_url = base_url
        self.token = None
        self.token_expires = None
        self.current_session = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent"""
        logger = logging.getLogger(f"agent.{self.agent_name}")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def authenticate(self) -> bool:
        """Authenticate with identity service"""
        try:
            self.logger.info("Authenticating with identity service...")
            response = requests.post(
                f"{self.base_url}:10002/v1/tokens/service",
                json={
                    "service_name": self.agent_name,
                    "scopes": ["agent:execute", "session:create", "memory:read"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers, refreshing token if needed"""
        if not self.token or datetime.now() >= self.token_expires:
            if not self.authenticate():
                raise Exception("Failed to authenticate")
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": f"SomaAgent01/{self.agent_name}"
        }
    
    def create_session(self, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new agent session"""
        default_config = {
            "timeout_seconds": 300,
            "memory_enabled": True,
            "tools_enabled": ["web_search", "file_operations"],
            "max_iterations": 10
        }
        
        session_config = {**default_config, **(config or {})}
        
        try:
            self.logger.info("Creating new session...")
            response = requests.post(
                f"{self.base_url}:10000/v1/sessions",
                headers=self.get_auth_headers(),
                json={
                    "agent_type": "automation",
                    "session_config": session_config
                },
                timeout=30
            )
            
            if response.status_code == 201:
                session_data = response.json()
                session_id = session_data["session_id"]
                self.current_session = session_id
                self.logger.info(f"Session created: {session_id}")
                return session_id
            else:
                self.logger.error(f"Session creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
            return None
    
    def execute_task(self, task_description: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Execute a task through the orchestrator"""
        if not session_id:
            session_id = self.current_session
            
        if not session_id:
            self.logger.error("No active session for task execution")
            return None
        
        try:
            self.logger.info(f"Executing task: {task_description[:50]}...")
            response = requests.post(
                f"{self.base_url}:10001/v1/workflows/execute",
                headers=self.get_auth_headers(),
                json={
                    "workflow_type": "agent_task",
                    "session_id": session_id,
                    "task": {
                        "type": "general",
                        "description": task_description,
                        "priority": "normal",
                        "timeout_seconds": 120
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Task executed successfully - Workflow: {result.get('workflow_id')}")
                return result
            else:
                self.logger.error(f"Task execution failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Task execution error: {e}")
            return None
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running workflow"""
        try:
            response = requests.get(
                f"{self.base_url}:10001/v1/workflows/{workflow_id}",
                headers=self.get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get workflow status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Workflow status error: {e}")
            return None
    
    def wait_for_workflow(self, workflow_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for workflow completion with polling"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_workflow_status(workflow_id)
            if not status:
                return None
                
            workflow_status = status.get("status")
            if workflow_status in ["completed", "failed", "cancelled"]:
                self.logger.info(f"Workflow {workflow_id} finished with status: {workflow_status}")
                return status
            
            self.logger.info(f"Workflow {workflow_id} status: {workflow_status}, waiting...")
            time.sleep(5)
        
        self.logger.warning(f"Workflow {workflow_id} timeout after {timeout}s")
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        services = {
            "gateway": f"{self.base_url}:10000/healthz",
            "orchestrator": f"{self.base_url}:10001/ready",
            "identity": f"{self.base_url}:10002/health"
        }
        
        health_status = {}
        
        for service, url in services.items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                health_status[service] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": round(response_time, 3),
                    "status_code": response.status_code
                }
            except Exception as e:
                health_status[service] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    def cleanup_session(self, session_id: Optional[str] = None) -> bool:
        """Clean up agent session"""
        if not session_id:
            session_id = self.current_session
            
        if not session_id:
            return True
        
        try:
            response = requests.delete(
                f"{self.base_url}:10000/v1/sessions/{session_id}",
                headers=self.get_auth_headers(),
                timeout=30
            )
            
            if response.status_code in [200, 204, 404]:  # 404 is OK - already deleted
                self.logger.info(f"Session {session_id} cleaned up")
                if session_id == self.current_session:
                    self.current_session = None
                return True
            else:
                self.logger.error(f"Session cleanup failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Session cleanup error: {e}")
            return False
    
    def run_agent_loop(self, tasks: list, cleanup: bool = True):
        """Run agent with a list of tasks"""
        try:
            # Health check first
            health = self.health_check()
            unhealthy_services = [svc for svc, status in health.items() if status["status"] != "healthy"]
            
            if unhealthy_services:
                self.logger.error(f"Unhealthy services detected: {unhealthy_services}")
                return False
            
            self.logger.info("All services healthy, starting agent loop")
            
            # Create session
            session_id = self.create_session()
            if not session_id:
                return False
            
            # Execute tasks
            results = []
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"Executing task {i}/{len(tasks)}")
                result = self.execute_task(task, session_id)
                
                if result:
                    # Wait for completion if workflow was started
                    workflow_id = result.get("workflow_id")
                    if workflow_id:
                        final_result = self.wait_for_workflow(workflow_id)
                        results.append(final_result)
                    else:
                        results.append(result)
                else:
                    self.logger.error(f"Task {i} failed, continuing...")
                    results.append(None)
                
                # Brief pause between tasks
                time.sleep(1)
            
            self.logger.info(f"Agent loop completed. {len([r for r in results if r])} successful tasks")
            return results
            
        finally:
            # Cleanup session
            if cleanup and self.current_session:
                self.cleanup_session()

# Example usage
if __name__ == "__main__":
    # Create and run SomaAgent01
    agent = SomaAgent01("demo-agent")
    
    # Define tasks to execute
    tasks = [
        "Check the current system status and report any issues",
        "Analyze recent log entries for any error patterns",
        "Generate a summary of system health metrics"
    ]
    
    # Run the agent
    results = agent.run_agent_loop(tasks)
    
    # Print results
    print("\n" + "="*50)
    print("SOMAAGENT01 EXECUTION SUMMARY")
    print("="*50)
    
    for i, result in enumerate(results, 1):
        if result:
            print(f"Task {i}: ✅ SUCCESS")
            print(f"  Status: {result.get('status', 'unknown')}")
            if 'result' in result:
                print(f"  Result: {str(result['result'])[:100]}...")
        else:
            print(f"Task {i}: ❌ FAILED")
    
    print("="*50)
```

---

## 🔧 Advanced Features

### Error Handling with Retries

**Robust Error Handling:**
```python
import time
from functools import wraps

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator

# Apply to critical methods
class RobustSomaAgent01(SomaAgent01):
    @retry_on_failure(max_retries=3, delay=2.0)
    def authenticate(self):
        return super().authenticate()
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def create_session(self, config=None):
        return super().create_session(config)
    
    @retry_on_failure(max_retries=2, delay=1.5)
    def execute_task(self, task_description, session_id=None):
        return super().execute_task(task_description, session_id)
```

### Memory Integration

**Agent Memory Usage:**
```python
def store_memory(self, key: str, data: Any, session_id: Optional[str] = None) -> bool:
    """Store data in agent memory"""
    if not session_id:
        session_id = self.current_session
    
    try:
        response = requests.put(
            f"{self.base_url}:10021/kv/{session_id}:{key}",
            headers=self.get_auth_headers(),
            json={"data": data, "timestamp": datetime.now().isoformat()},
            timeout=30
        )
        
        return response.status_code == 200
    except Exception as e:
        self.logger.error(f"Memory storage error: {e}")
        return False

def retrieve_memory(self, key: str, session_id: Optional[str] = None) -> Optional[Any]:
    """Retrieve data from agent memory"""
    if not session_id:
        session_id = self.current_session
    
    try:
        response = requests.get(
            f"{self.base_url}:10021/kv/{session_id}:{key}",
            headers=self.get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("data")
        return None
    except Exception as e:
        self.logger.error(f"Memory retrieval error: {e}")
        return None

# Add to SomaAgent01 class
SomaAgent01.store_memory = store_memory
SomaAgent01.retrieve_memory = retrieve_memory
```

### Async Agent Implementation

**Asynchronous SomaAgent01:**
```python
import asyncio
import aiohttp
from typing import List

class AsyncSomaAgent01:
    """Asynchronous version of SomaAgent01 for high-performance scenarios"""
    
    def __init__(self, agent_name: str, base_url: str = "http://localhost"):
        self.agent_name = agent_name
        self.base_url = base_url
        self.token = None
        self.token_expires = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Async authentication"""
        try:
            async with self.session.post(
                f"{self.base_url}:10002/v1/tokens/service",
                json={
                    "service_name": self.agent_name,
                    "scopes": ["agent:execute", "session:create"]
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data["access_token"]
                    self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
                    return True
                return False
        except Exception as e:
            print(f"Auth error: {e}")
            return False
    
    async def execute_multiple_tasks(self, tasks: List[str]) -> List[Dict]:
        """Execute multiple tasks concurrently"""
        # Create session first
        session_id = await self.create_session()
        if not session_id:
            return []
        
        # Execute tasks concurrently
        task_coroutines = [
            self.execute_task(task, session_id) 
            for task in tasks
        ]
        
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Clean up session
        await self.cleanup_session(session_id)
        
        return results

# Usage example
async def run_async_agent():
    async with AsyncSomaAgent01("async-agent") as agent:
        tasks = [
            "Check system health",
            "Analyze performance metrics",
            "Generate status report"
        ]
        results = await agent.execute_multiple_tasks(tasks)
        return results

# Run async agent
# results = asyncio.run(run_async_agent())
```

---

## 📊 Testing Your Agent

### Unit Tests for SomaAgent01

**Test Implementation:**
```python
import unittest
from unittest.mock import Mock, patch
import json

class TestSomaAgent01(unittest.TestCase):
    def setUp(self):
        self.agent = SomaAgent01("test-agent")
    
    @patch('requests.post')
    def test_authentication_success(self, mock_post):
        # Mock successful authentication response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        # Test authentication
        result = self.agent.authenticate()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.agent.token, "test_token")
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_authentication_failure(self, mock_post):
        # Mock failed authentication response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Test authentication
        result = self.agent.authenticate()
        
        # Assertions
        self.assertFalse(result)
        self.assertIsNone(self.agent.token)
    
    @patch('requests.post')
    def test_session_creation(self, mock_post):
        # Setup authentication
        self.agent.token = "test_token"
        self.agent.token_expires = datetime.now() + timedelta(hours=1)
        
        # Mock session creation response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"session_id": "test_session"}
        mock_post.return_value = mock_response
        
        # Test session creation
        session_id = self.agent.create_session()
        
        # Assertions
        self.assertEqual(session_id, "test_session")
        self.assertEqual(self.agent.current_session, "test_session")
    
    def test_health_check(self):
        with patch('requests.get') as mock_get:
            # Mock health check responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Test health check
            health = self.agent.health_check()
            
            # Assertions
            self.assertIn("gateway", health)
            self.assertIn("orchestrator", health)
            self.assertIn("identity", health)
            self.assertEqual(health["gateway"]["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

**Integration Test Script:**
```python
#!/usr/bin/env python3
"""
Integration test for SomaAgent01
Requires SomaAgentHub services to be running
"""

import sys
import time
from soma_agent_01 import SomaAgent01

def test_full_agent_workflow():
    """Test complete agent workflow"""
    print("🧪 Starting SomaAgent01 Integration Test")
    print("="*50)
    
    # Initialize agent
    agent = SomaAgent01("integration-test-agent")
    
    try:
        # Test 1: Health Check
        print("1️⃣ Testing health check...")
        health = agent.health_check()
        unhealthy = [svc for svc, status in health.items() if status["status"] != "healthy"]
        
        if unhealthy:
            print(f"❌ Unhealthy services: {unhealthy}")
            return False
        print("✅ All services healthy")
        
        # Test 2: Authentication
        print("2️⃣ Testing authentication...")
        if not agent.authenticate():
            print("❌ Authentication failed")
            return False
        print("✅ Authentication successful")
        
        # Test 3: Session Creation
        print("3️⃣ Testing session creation...")
        session_id = agent.create_session()
        if not session_id:
            print("❌ Session creation failed")
            return False
        print(f"✅ Session created: {session_id}")
        
        # Test 4: Task Execution
        print("4️⃣ Testing task execution...")
        result = agent.execute_task("Test task: return current timestamp")
        if not result:
            print("❌ Task execution failed")
            return False
        print(f"✅ Task executed: {result.get('workflow_id')}")
        
        # Test 5: Workflow Status
        print("5️⃣ Testing workflow status...")
        workflow_id = result.get("workflow_id")
        if workflow_id:
            status = agent.get_workflow_status(workflow_id)
            if status:
                print(f"✅ Workflow status: {status.get('status')}")
            else:
                print("⚠️ Could not get workflow status")
        
        # Test 6: Session Cleanup
        print("6️⃣ Testing session cleanup...")
        if agent.cleanup_session():
            print("✅ Session cleaned up")
        else:
            print("⚠️ Session cleanup failed")
        
        print("="*50)
        print("🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    finally:
        # Ensure cleanup
        if agent.current_session:
            agent.cleanup_session()

if __name__ == "__main__":
    success = test_full_agent_workflow()
    sys.exit(0 if success else 1)
```

---

## 🚀 Production Deployment

### Docker Container for SomaAgent01

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY soma_agent_01.py .
COPY config.json .

# Create non-root user
RUN useradd --create-home --shell /bin/bash agent
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from soma_agent_01 import SomaAgent01; agent = SomaAgent01('health-check'); print('healthy' if agent.health_check() else exit(1))"

# Run agent
CMD ["python", "soma_agent_01.py"]
```

**requirements.txt:**
```
requests>=2.31.0
aiohttp>=3.8.0
prometheus-client>=0.17.0
cryptography>=41.0.0
```

### Kubernetes Deployment

**soma-agent-01-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: soma-agent-01
  namespace: soma-agent-hub
  labels:
    app: soma-agent-01
    version: v1.0.0
spec:
  replicas: 1
  selector:
    matchLabels:
      app: soma-agent-01
  template:
    metadata:
      labels:
        app: soma-agent-01
        version: v1.0.0
    spec:
      serviceAccountName: soma-agent-01
      containers:
      - name: soma-agent-01
        image: somaagent/soma-agent-01:latest
        env:
        - name: AGENT_NAME
          value: "production-soma-agent-01"
        - name: SOMA_BASE_URL
          value: "http://gateway-api:8000"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: soma-agent-01
  namespace: soma-agent-hub

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: soma-agent-01-role
  namespace: soma-agent-hub
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: soma-agent-01-binding
  namespace: soma-agent-hub
subjects:
- kind: ServiceAccount
  name: soma-agent-01
roleRef:
  kind: Role
  name: soma-agent-01-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 🔄 What's Next?

### Immediate Next Steps

1. **Test your SomaAgent01 implementation** with the integration test script
2. **Deploy to development environment** using Docker or Kubernetes
3. **Monitor agent performance** with health checks and metrics
4. **Implement error handling** for production resilience

### Advanced Agent Patterns

Once you have SomaAgent01 working, explore these advanced patterns:

- **[Propagation Agent](propagation-agent.md)** - Handle data propagation and event streaming
- **[Monitoring Agent](monitoring-agent.md)** - Implement comprehensive system monitoring
- **[Security Hardening](security-hardening.md)** - Advanced security practices for production

### Agent Development Resources

- **SomaAgentHub SDK**: Python client library with built-in patterns
- **Agent Templates**: Pre-built agent templates for common use cases
- **Testing Framework**: Comprehensive testing tools for agent development
- **Monitoring Dashboard**: Real-time agent performance monitoring

---

**Congratulations! You've successfully created your first autonomous agent with SomaAgentHub. Your SomaAgent01 can now authenticate, create sessions, execute tasks, and handle errors gracefully. Ready for the next challenge? Try building a [Propagation Agent](propagation-agent.md) to handle real-time data processing.**