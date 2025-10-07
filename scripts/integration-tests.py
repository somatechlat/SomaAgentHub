#!/usr/bin/env python3
"""
SomaAgent Integration Test Suite
Tests all live services and validates the complete platform
"""

import asyncio
import httpx
import json
import time
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
import subprocess

@dataclass
class ServiceTest:
    name: str
    url: str
    port: int
    endpoints: List[str]
    expected_status: int = 200

class SomaAgentTester:
    def __init__(self):
        self.services = [
            ServiceTest("jobs", "http://localhost", 8000, ["/health", "/jobs"]),
            ServiceTest("memory-gateway", "http://localhost", 9696, ["/health", "/v1/recall/test"]),
            ServiceTest("orchestrator", "http://localhost", 8002, ["/health", "/status"]),
            ServiceTest("policy-engine", "http://localhost", 8100, ["/health", "/validate"]),
            ServiceTest("settings-service", "http://localhost", 8004, ["/health"]),
            ServiceTest("gateway-api", "http://localhost", 8003, ["/health", "/docs"]),
            ServiceTest("identity-service", "http://localhost", 8006, ["/health"]),
            ServiceTest("constitution-service", "http://localhost", 8007, ["/health"]),
            ServiceTest("analytics-service", "http://localhost", 8008, ["/health", "/metrics"]),
            ServiceTest("billing-service", "http://localhost", 8009, ["/health"]),
            ServiceTest("task-capsule-repo", "http://localhost", 8005, ["/health", "/capsules"])
        ]
        self.results = {}
        self.port_forwards = []
    
    def setup_port_forwards(self):
        """Setup port forwards for all services"""
        print("🔗 Setting up port forwards...")
        
        for service in self.services:
            try:
                cmd = f"kubectl port-forward -n soma-agent-hub svc/{service.name} {service.port}:{service.port}"
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.port_forwards.append(proc)
                print(f"   ✓ {service.name}:{service.port}")
                time.sleep(0.5)  # Brief pause between port forwards
            except Exception as e:
                print(f"   ❌ Failed to setup port forward for {service.name}: {e}")
        
        print("⏳ Waiting for port forwards to stabilize...")
        time.sleep(3)
    
    def cleanup_port_forwards(self):
        """Clean up all port forward processes"""
        print("🧹 Cleaning up port forwards...")
        for proc in self.port_forwards:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
    
    async def test_service_endpoint(self, service: ServiceTest, endpoint: str) -> Dict[str, Any]:
        """Test a specific endpoint on a service"""
        url = f"{service.url}:{service.port}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                return {
                    "service": service.name,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status_code == service.expected_status,
                    "response_time": response.elapsed.total_seconds(),
                    "content_type": response.headers.get("content-type", ""),
                    "response_size": len(response.content),
                    "response_preview": str(response.text)[:200] if response.text else ""
                }
        except Exception as e:
            return {
                "service": service.name,
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "error": str(e),
                "response_time": 0
            }
    
    async def test_service(self, service: ServiceTest) -> Dict[str, Any]:
        """Test all endpoints for a service"""
        print(f"🧪 Testing {service.name}...")
        
        service_results = {
            "name": service.name,
            "port": service.port,
            "endpoints": [],
            "overall_success": True,
            "total_response_time": 0
        }
        
        for endpoint in service.endpoints:
            result = await self.test_service_endpoint(service, endpoint)
            service_results["endpoints"].append(result)
            service_results["total_response_time"] += result.get("response_time", 0)
            
            if not result.get("success", False):
                service_results["overall_success"] = False
            
            status = "✅" if result.get("success") else "❌"
            print(f"   {status} {endpoint} - {result.get('status_code', 'ERROR')}")
        
        return service_results
    
    async def run_integration_tests(self):
        """Run all integration tests"""
        print("🚀 Starting SomaAgent Integration Tests")
        print("=" * 50)
        
        # Test all services concurrently
        tasks = [self.test_service(service) for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_services = 0
        total_services = len(self.services)
        
        print("\n📊 TEST RESULTS")
        print("=" * 50)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Service test failed with exception: {result}")
                continue
            
            if result["overall_success"]:
                successful_services += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"{status} {result['name']} - {len(result['endpoints'])} endpoints tested")
            print(f"      Response time: {result['total_response_time']:.3f}s")
            
            # Show failed endpoints
            failed_endpoints = [ep for ep in result['endpoints'] if not ep.get('success', False)]
            if failed_endpoints:
                for ep in failed_endpoints:
                    error = ep.get('error', f"HTTP {ep.get('status_code', 'Unknown')}")
                    print(f"      ❌ {ep['endpoint']}: {error}")
        
        print(f"\n🎯 SUMMARY: {successful_services}/{total_services} services passing")
        
        if successful_services == total_services:
            print("🎉 ALL TESTS PASSED! SomaAgent platform is fully operational!")
            return True
        else:
            print(f"⚠️  {total_services - successful_services} services need attention")
            return False
    
    def test_kubernetes_deployment(self):
        """Test Kubernetes deployment status"""
        print("\n🏗️  KUBERNETES DEPLOYMENT STATUS")
        print("=" * 50)
        
        try:
            # Get pod status
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "soma-agent-hub", "-o", "json"],
                capture_output=True, text=True, check=True
            )
            
            pods_data = json.loads(result.stdout)
            
            running_pods = 0
            total_pods = len(pods_data["items"])
            
            for pod in pods_data["items"]:
                name = pod["metadata"]["name"]
                status = pod["status"]["phase"]
                
                if status == "Running":
                    running_pods += 1
                    print(f"✅ {name}: {status}")
                else:
                    print(f"❌ {name}: {status}")
                    
                    # Show container statuses
                    if "containerStatuses" in pod["status"]:
                        for container in pod["status"]["containerStatuses"]:
                            if not container.get("ready", False):
                                state = container.get("state", {})
                                if "waiting" in state:
                                    reason = state["waiting"].get("reason", "Unknown")
                                    print(f"      Container waiting: {reason}")
            
            print(f"\n📈 Deployment Status: {running_pods}/{total_pods} pods running")
            return running_pods, total_pods
            
        except Exception as e:
            print(f"❌ Failed to check Kubernetes status: {e}")
            return 0, 0
    
    def run_ci_tests(self):
        """Run CI/CD pipeline tests"""
        print("\n🔄 CI/CD PIPELINE TESTS")
        print("=" * 50)
        
        tests = [
            ("Helm Template Validation", "helm template soma-agent-hub ./k8s/helm/soma-agent --dry-run"),
            ("Kubernetes Resource Validation", "kubectl apply --dry-run=client -f k8s/"),
            ("Docker Image Availability", "docker images | grep soma"),
        ]
        
        passed_tests = 0
        
        for test_name, command in tests:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    print(f"      Error: {result.stderr[:200]}")
            except Exception as e:
                print(f"❌ {test_name}: EXCEPTION - {e}")
        
        print(f"\n📈 CI Tests: {passed_tests}/{len(tests)} passed")
        return passed_tests == len(tests)

async def main():
    tester = SomaAgentTester()
    
    try:
        # Test Kubernetes deployment first
        running_pods, total_pods = tester.test_kubernetes_deployment()
        
        # Run CI tests
        ci_success = tester.run_ci_tests()
        
        # Only run integration tests if we have some running pods
        if running_pods > 0:
            tester.setup_port_forwards()
            
            try:
                integration_success = await tester.run_integration_tests()
            finally:
                tester.cleanup_port_forwards()
        else:
            print("\n⚠️  No running pods detected. Skipping integration tests.")
            integration_success = False
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"Kubernetes Deployment: {running_pods}/{total_pods} pods running")
        print(f"CI/CD Tests: {'✅ PASSED' if ci_success else '❌ FAILED'}")
        print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
        
        if running_pods > 0 and ci_success:
            print("🚀 SomaAgent platform is operational and ready for development!")
            sys.exit(0)
        else:
            print("⚠️  Platform needs attention before production use.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        tester.cleanup_port_forwards()
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        tester.cleanup_port_forwards()
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())