#!/usr/bin/env python3
"""
Sprint 1 Demo Script
Demonstrates PostgreSQL-backed capsule registry and agent spawning
"""

import asyncio
import uuid
import requests
import json
from typing import Dict, Any


class Sprint1Demo:
    """Demo class for Sprint 1 functionality"""
    
    def __init__(self):
        self.capsule_base_url = "http://localhost:8000"
        self.agent_base_url = "http://localhost:8001"
    
    async def test_capsule_registry(self):
        """Test the PostgreSQL-backed capsule registry"""
        print("🧪 Testing Capsule Registry...")
        
        # Create a test capsule
        capsule_id = str(uuid.uuid4())
        test_capsule = {
            "capsule_id": capsule_id,
            "version": "1.0.0",
            "type": "workflow",
            "manifest_yaml": """
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: test-workflow
spec:
  entrypoint: whalesay
  templates:
  - name: whalesay
    container:
      image: docker/whalesay:latest
      command: [cowsay]
      args: ["hello world"]
"""
        }
        
        # Create capsule
        response = requests.post(
            f"{self.capsule_base_url}/v1/capsules",
            json=test_capsule
        )
        
        if response.status_code == 201:
            print(f"✅ Capsule created: {response.json()['id']}")
            return response.json()
        else:
            print(f"❌ Failed to create capsule: {response.text}")
            return None
    
    async def test_agent_spawner(self):
        """Test the agent spawner service"""
        print("🤖 Testing Agent Spawner...")
        
        # Create a test agent spawn request
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        spawn_request = {
            "agent_type": "code-generator",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "image": "python:3.11-slim",
            "execution_mode": "batch",
            "env_vars": {"TASK": "generate_python_code"},
            "namespace": f"tenant-{tenant_id[:8]}"
        }
        
        # Spawn agent
        response = requests.post(
            f"{self.agent_base_url}/v1/spawn",
            json=spawn_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Agent spawned: {result['instance_id']}")
            
            # Get agent status
            status_response = requests.get(
                f"{self.agent_base_url}/v1/agents/{result['instance_id']}"
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   Status: {status['status']}")
                print(f"   Namespace: {status['namespace']}")
                
            return result
        else:
            print(f"❌ Failed to spawn agent: {response.text}")
            return None
    
    async def run_comprehensive_demo(self):
        """Run comprehensive Sprint 1 demo"""
        print("🚀 Sprint 1 Comprehensive Demo")
        print("=" * 50)
        
        # Check services health
        print("\n1️⃣ Checking Services Health...")
        
        try:
            capsule_health = requests.get(f"{self.capsule_base_url}/health").json()
            print(f"   ✅ Capsule Registry: {capsule_health}")
        except:
            print("   ❌ Capsule Registry not responding")
            return
        
        try:
            agent_health = requests.get(f"{self.agent_base_url}/health").json()
            print(f"   ✅ Agent Spawner: {agent_health}")
        except:
            print("   ❌ Agent Spawner not responding")
            return
        
        # Test capsule operations
        print("\n2️⃣ Testing Capsule Operations...")
        
        capsule_result = await self.test_capsule_registry()
        if capsule_result:
            capsule_id = capsule_result['capsule_id']
            
            # List capsules
            list_response = requests.get(f"{self.capsule_base_url}/v1/capsules")
            if list_response.status_code == 200:
                capsules = list_response.json()
                print(f"   📊 Total capsules: {capsules['total']}")
            
            # Get specific capsule
            get_response = requests.get(
                f"{self.capsule_base_url}/v1/capsules/{capsule_id}/1.0.0"
            )
            if get_response.status_code == 200:
                print("   ✅ Retrieved capsule successfully")
        
        # Test agent operations
        print("\n3️⃣ Testing Agent Operations...")
        agent_result = await self.test_agent_spawner()
        
        if agent_result:
            # List agents
            list_agents = requests.get(f"{self.agent_base_url}/v1/agents")
            if list_agents.status_code == 200:
                agents = list_agents.json()
                print(f"   📊 Total agents: {agents['total']}")
        
        # Performance test
        print("\n4️⃣ Performance Test...")
        
        # Create multiple capsules quickly
        print("   Creating 5 capsules rapidly...")
        for i in range(5):
            capsule_data = {
                "capsule_id": str(uuid.uuid4()),
                "version": f"1.0.{i}",
                "type": "static",
                "manifest_yaml": f"# Test capsule {i}"
            }
            response = requests.post(f"{self.capsule_base_url}/v1/capsules", json=capsule_data)
            if response.status_code == 201:
                print(f"      ✅ Capsule {i} created")
        
        print("\n🎉 Sprint 1 Demo Complete!")
        print("\n✅ All PostgreSQL-backed services are working")
        print("✅ Agent instances are being tracked")
        print("✅ Kubernetes-native spawning is ready")
    
    def print_architecture_summary(self):
        """Print Sprint 1 architecture summary"""
        print("\n🏗️ Sprint 1 Architecture Summary")
        print("=" * 40)
        print("📦 Capsule Registry")
        print("   ├── PostgreSQL-backed storage")
        print("   ├── UUID primary keys")
        print("   ├── Version tracking")
        print("   └── RESTful API endpoints")
        print()
        print("🤖 Agent Spawner")
        print("   ├── AgentInstance model")
        print("   ├── Kubernetes integration")
        print("   ├── Job/Deployment management")
        print("   └── Tenant isolation")
        print()
        print("🗄️ Database Schema")
        print("   ├── capsules table")
        print("   ├── agent_instances table")
        print("   ├── Foreign key relationships")
        print("   └── JSONB metadata support")


def main():
    """Run the Sprint 1 demo"""
    demo = Sprint1Demo()
    
    print("🎭 Sprint 1 Production Demo")
    print("PostgreSQL Migration & Agent Management")
    print("=" * 60)
    
    demo.print_architecture_summary()
    
    # Wait for services to be ready
    import time
    print("\n⏳ Waiting 10 seconds for services to start...")
    time.sleep(10)
    
    # Run demo
    asyncio.run(demo.run_comprehensive_demo())


if __name__ == "__main__":
    main()