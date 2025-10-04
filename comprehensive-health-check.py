#!/usr/bin/env python3
"""
Comprehensive SomaAgent platform integration test and health check
Identifies services that need fixes and provides detailed error analysis
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import httpx
import subprocess


class SomaAgentTester:
    def __init__(self):
        self.services = {
            "analytics-service": "http://localhost:30001",
            "billing-service": "http://localhost:30002", 
            "constitution-service": "http://localhost:30003",
            "gateway-api": "http://localhost:30004",
            "identity-service": "http://localhost:30005",
            "jobs": "http://localhost:30006",
            "memory-gateway": "http://localhost:30007",
            "orchestrator": "http://localhost:30008",
            "policy-engine": "http://localhost:30009",
            "settings-service": "http://localhost:30010",
            "slm-service": "http://localhost:30011",
            "task-capsule-repo": "http://localhost:30012"
        }
        self.results = {}
        self.error_analysis = {}
    
    def setup_port_forwards(self):
        """Setup kubectl port forwards for all services"""
        port_mappings = [
            ("analytics-service", 30001, 8000),
            ("billing-service", 30002, 8000),
            ("constitution-service", 30003, 8000),
            ("gateway-api", 30004, 8000),
            ("identity-service", 30005, 8000),
            ("jobs", 30006, 8000),
            ("memory-gateway", 30007, 8000),
            ("orchestrator", 30008, 8000),
            ("policy-engine", 30009, 8000),
            ("settings-service", 30010, 8000),
            ("slm-service", 30011, 8000),
            ("task-capsule-repo", 30012, 8000)
        ]
        
        processes = []
        for service, local_port, remote_port in port_mappings:
            cmd = f"kubectl port-forward deployment/{service} {local_port}:{remote_port} -n soma-agent"
            proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append((service, proc))
        
        # Give port forwards time to establish
        asyncio.sleep(5)
        return processes

    def get_pod_logs(self, service_name: str) -> str:
        """Get the logs for a service deployment"""
        try:
            result = subprocess.run(
                f"kubectl logs deployment/{service_name} -n soma-agent --tail=20".split(),
                capture_output=True, text=True, timeout=10
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting logs: {str(e)}"

    def get_pod_status(self, service_name: str) -> Dict:
        """Get detailed pod status for a service"""
        try:
            result = subprocess.run(
                f"kubectl get pods -l app={service_name} -n soma-agent -o json".split(),
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data["items"]:
                    pod = data["items"][0]
                    return {
                        "phase": pod["status"]["phase"],
                        "ready": pod["status"]["containerStatuses"][0]["ready"] if "containerStatuses" in pod["status"] else False,
                        "restartCount": pod["status"]["containerStatuses"][0]["restartCount"] if "containerStatuses" in pod["status"] else 0,
                        "image": pod["spec"]["containers"][0]["image"]
                    }
        except Exception as e:
            return {"error": str(e)}
        return {"error": "No pods found"}

    async def test_service_health(self, service_name: str, url: str) -> Dict:
        """Test individual service health with detailed diagnostics"""
        result = {
            "service": service_name,
            "url": url,
            "status": "unknown",
            "response_time": None,
            "error": None,
            "pod_status": None,
            "logs": None
        }
        
        # Get pod status first
        result["pod_status"] = self.get_pod_status(service_name)
        
        # If pod is not ready, get logs for diagnosis
        if not result["pod_status"].get("ready", False):
            result["logs"] = self.get_pod_logs(service_name)
            result["status"] = "pod_not_ready"
            
            # Analyze common error patterns in logs
            if "ModuleNotFoundError" in result["logs"]:
                missing_modules = []
                for line in result["logs"].split("\n"):
                    if "ModuleNotFoundError: No module named" in line:
                        module = line.split("'")[1] if "'" in line else "unknown"
                        missing_modules.append(module)
                result["error"] = f"Missing Python modules: {', '.join(set(missing_modules))}"
            elif "ImportError" in result["logs"]:
                result["error"] = "Import error - check dependencies"
            elif "FileNotFoundError" in result["logs"]:
                result["error"] = "Missing files - check application structure"
            elif "PermissionError" in result["logs"]:
                result["error"] = "Permission issues"
            elif result["logs"]:
                # Try to extract the last error line
                lines = [l.strip() for l in result["logs"].split("\n") if l.strip()]
                if lines:
                    result["error"] = lines[-1]
            
            return result

        # If pod is ready, test HTTP health endpoint
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start_time = datetime.now()
                response = await client.get(f"{url}/health")
                end_time = datetime.now()
                
                result["response_time"] = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    result["status"] = "healthy"
                    try:
                        data = response.json()
                        result["version"] = data.get("version", "unknown")
                        result["service_details"] = data
                    except:
                        pass
                else:
                    result["status"] = "unhealthy"
                    result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                    
        except httpx.ConnectError:
            result["status"] = "connection_failed"
            result["error"] = "Cannot connect to service - port forward or service issues"
        except httpx.TimeoutException:
            result["status"] = "timeout"
            result["error"] = "Service responding too slowly"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        return result

    async def run_comprehensive_test(self) -> Dict:
        """Run comprehensive platform health check"""
        print("🚀 Starting SomaAgent Platform Comprehensive Health Check...")
        print(f"Testing {len(self.services)} services...")
        
        # Set up port forwards
        print("Setting up kubectl port forwards...")
        port_processes = self.setup_port_forwards()
        
        try:
            # Wait for port forwards to be ready
            await asyncio.sleep(8)
            
            # Test all services concurrently
            tasks = [
                self.test_service_health(service, url) 
                for service, url in self.services.items()
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Organize results
            healthy_count = 0
            unhealthy_count = 0
            error_count = 0
            dependency_issues = []
            
            for result in results:
                self.results[result["service"]] = result
                
                if result["status"] == "healthy":
                    healthy_count += 1
                elif result["status"] in ["unhealthy", "connection_failed", "timeout"]:
                    unhealthy_count += 1
                else:
                    error_count += 1
                
                # Collect dependency issues
                if "Missing Python modules" in str(result.get("error", "")):
                    dependency_issues.append({
                        "service": result["service"],
                        "modules": result["error"]
                    })
            
            # Generate summary
            total = len(self.services)
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_services": total,
                "healthy": healthy_count,
                "unhealthy": unhealthy_count, 
                "errors": error_count,
                "success_rate": f"{(healthy_count/total)*100:.1f}%",
                "dependency_issues_count": len(dependency_issues),
                "services": self.results,
                "dependency_analysis": dependency_issues,
                "recommendations": self.generate_recommendations()
            }
            
            return summary
            
        finally:
            # Clean up port forwards
            print("Cleaning up port forwards...")
            for service, proc in port_processes:
                proc.terminate()
                
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Count different types of issues
        dependency_issues = 0
        connection_issues = 0
        pod_issues = 0
        
        for service, result in self.results.items():
            if "Missing Python modules" in str(result.get("error", "")):
                dependency_issues += 1
            elif result["status"] == "connection_failed":
                connection_issues += 1
            elif result["status"] == "pod_not_ready":
                pod_issues += 1
        
        if dependency_issues > 0:
            recommendations.append(f"🔧 Fix missing Python dependencies in {dependency_issues} services by updating requirements.txt files")
            
        if pod_issues > 0:
            recommendations.append(f"🚀 Rebuild and redeploy {pod_issues} services with updated Docker images")
            
        if connection_issues > 0:
            recommendations.append(f"🔌 Check Kubernetes service configurations for {connection_issues} services")
            
        # Add specific recommendations
        recommendations.extend([
            "📦 Run: docker build && kind load docker-image && kubectl rollout restart",
            "🔍 Check logs: kubectl logs deployment/<service-name> -n soma-agent",
            "🎯 Focus on getting analytics-service and memory-gateway patterns working first",
            "⚡ Test individual services: curl http://localhost:3000X/health"
        ])
        
        return recommendations

    def print_detailed_report(self, summary: Dict):
        """Print comprehensive test report"""
        print("\n" + "="*80)
        print("🎯 SOMAAGENT PLATFORM HEALTH REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Services: {summary['total_services']}")
        print(f"   ✅ Healthy: {summary['healthy']}")
        print(f"   ⚠️  Unhealthy: {summary['unhealthy']}")
        print(f"   ❌ Errors: {summary['errors']}")
        print(f"   📈 Success Rate: {summary['success_rate']}")
        
        print(f"\n🔧 SERVICE STATUS:")
        for service, result in summary['services'].items():
            status = result['status']
            icon = "✅" if status == "healthy" else "❌"
            response_time = f" ({result['response_time']:.3f}s)" if result['response_time'] else ""
            
            print(f"   {icon} {service:<20} {status.upper()}{response_time}")
            if result.get('error'):
                print(f"      └── Error: {result['error'][:100]}...")
        
        if summary['dependency_analysis']:
            print(f"\n🚨 DEPENDENCY ISSUES:")
            for issue in summary['dependency_analysis']:
                print(f"   • {issue['service']}: {issue['modules']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"   {i}. {rec}")
            
        print(f"\n⏰ Test completed at: {summary['timestamp']}")
        print("="*80)


async def main():
    """Main test execution"""
    tester = SomaAgentTester()
    
    try:
        summary = await tester.run_comprehensive_test()
        tester.print_detailed_report(summary)
        
        # Exit with appropriate code
        if summary['healthy'] == summary['total_services']:
            print("\n🎉 All services are healthy! Platform is fully operational.")
            sys.exit(0)
        elif summary['healthy'] > 0:
            print(f"\n⚡ {summary['healthy']}/{summary['total_services']} services operational. Continue fixing remaining issues.")
            sys.exit(1)
        else:
            print("\n🚨 No services operational. Major fixes needed.")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ImportError as e:
        print(f"Missing required Python packages: {e}")
        print("Please install: pip install httpx")
        sys.exit(1)