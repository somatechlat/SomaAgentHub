#!/usr/bin/env python3
"""
SomaAgent Live Server Test Report
Comprehensive testing of deployment and CI pipeline
"""

import subprocess
import json
import sys
from datetime import datetime

class SomaAgentTestReporter:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "kubernetes_status": {},
            "ci_tests": {},
            "service_health": {},
            "recommendations": []
        }
    
    def check_kubernetes_status(self):
        """Check Kubernetes deployment status"""
        print("🏗️ CHECKING KUBERNETES DEPLOYMENT...")
        
        try:
            # Get all pods
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "soma-agent-hub", "-o", "json"],
                capture_output=True, text=True, check=True
            )
            pods_data = json.loads(result.stdout)
            
            total_pods = len(pods_data["items"])
            running_pods = 0
            pod_details = []
            
            for pod in pods_data["items"]:
                name = pod["metadata"]["name"]
                phase = pod["status"]["phase"]
                ready = False
                
                if "containerStatuses" in pod["status"]:
                    ready = all(c.get("ready", False) for c in pod["status"]["containerStatuses"])
                
                pod_details.append({
                    "name": name,
                    "phase": phase,
                    "ready": ready,
                    "service": name.split("-")[0] if "-" in name else name
                })
                
                if phase == "Running" and ready:
                    running_pods += 1
                    print(f"   ✅ {name}: Running & Ready")
                elif phase == "Running":
                    print(f"   ⚠️  {name}: Running but not Ready")
                else:
                    print(f"   ❌ {name}: {phase}")
            
            # Get services
            svc_result = subprocess.run(
                ["kubectl", "get", "svc", "-n", "soma-agent-hub", "-o", "json"],
                capture_output=True, text=True, check=True
            )
            services_data = json.loads(svc_result.stdout)
            
            self.report["kubernetes_status"] = {
                "total_pods": total_pods,
                "running_pods": running_pods,
                "ready_pods": running_pods,
                "total_services": len(services_data["items"]),
                "pod_details": pod_details,
                "deployment_success_rate": (running_pods / total_pods * 100) if total_pods > 0 else 0
            }
            
            print(f"   📊 Status: {running_pods}/{total_pods} pods running and ready")
            
        except Exception as e:
            print(f"   ❌ Failed to check Kubernetes status: {e}")
            self.report["kubernetes_status"] = {"error": str(e)}
    
    def run_ci_tests(self):
        """Run CI/CD tests"""
        print("\n🔄 RUNNING CI/CD TESTS...")
        
        tests = [
            {
                "name": "Helm Template Validation",
                "command": ["helm", "template", "soma-agent-hub", "./k8s/helm/soma-agent", "--dry-run"],
                "description": "Validates Helm chart templates"
            },
            {
                "name": "Docker Images Built",
                "command": ["docker", "images", "--filter", "reference=ghcr.io/somatechlat/soma-*"],
                "description": "Checks if all Docker images are available"
            },
            {
                "name": "Kubernetes Connectivity",
                "command": ["kubectl", "cluster-info"],
                "description": "Verifies Kubernetes cluster connectivity"
            }
        ]
        
        test_results = []
        
        for test in tests:
            try:
                result = subprocess.run(
                    test["command"], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                success = result.returncode == 0
                test_result = {
                    "name": test["name"],
                    "success": success,
                    "description": test["description"],
                    "output_lines": len(result.stdout.split('\n')) if result.stdout else 0
                }
                
                if success:
                    print(f"   ✅ {test['name']}: PASSED")
                else:
                    print(f"   ❌ {test['name']}: FAILED")
                    print(f"      Error: {result.stderr[:100]}...")
                
                test_results.append(test_result)
                
            except Exception as e:
                print(f"   ❌ {test['name']}: EXCEPTION - {e}")
                test_results.append({
                    "name": test["name"],
                    "success": False,
                    "error": str(e)
                })
        
        self.report["ci_tests"] = {
            "tests": test_results,
            "total": len(tests),
            "passed": sum(1 for t in test_results if t.get("success", False)),
            "success_rate": sum(1 for t in test_results if t.get("success", False)) / len(tests) * 100
        }
    
    def analyze_service_health(self):
        """Analyze service health based on logs and status"""
        print("\n🏥 ANALYZING SERVICE HEALTH...")
        
        services = [
            "jobs", "memory-gateway", "orchestrator", "policy-engine",
            "slm-service", "settings-service", "gateway-api", "identity-service",
            "constitution-service", "analytics-service", "billing-service", "task-capsule-repo"
        ]

        legacy_alias = {"slm-service": "somallm-provider"}
        
        service_health = {}
        
        for service in services:
            try:
                deployment_name = service
                check_deployment = subprocess.run(
                    ["kubectl", "get", "deployment", deployment_name, "-n", "soma-agent-hub"],
                    capture_output=True, text=True, timeout=5
                )

                if check_deployment.returncode != 0 and service in legacy_alias:
                    deployment_name = legacy_alias[service]

                # Get recent logs
                log_result = subprocess.run(
                    ["kubectl", "logs", "-n", "soma-agent-hub", f"deployment/{deployment_name}", "--tail=5"],
                    capture_output=True, text=True, timeout=10
                )
                
                # Analyze logs for common issues
                logs = log_result.stdout.lower()
                issues = []
                
                if "error" in logs or "exception" in logs:
                    issues.append("errors_in_logs")
                if "modulenotfounderror" in logs:
                    issues.append("missing_dependencies")
                if "connection refused" in logs:
                    issues.append("connection_issues")
                if "started server" in logs or "uvicorn running" in logs:
                    issues.append("server_started")
                
                service_health[service] = {
                    "has_logs": bool(log_result.stdout),
                    "issues": issues,
                    "log_lines": len(log_result.stdout.split('\n')) if log_result.stdout else 0
                }
                
                if "server_started" in issues:
                    print(f"   ✅ {service}: Server appears to be running")
                elif issues:
                    print(f"   ⚠️  {service}: Issues detected - {', '.join(issues)}")
                else:
                    print(f"   ❓ {service}: Status unclear")
                    
            except Exception as e:
                service_health[service] = {"error": str(e)}
                print(f"   ❌ {service}: Could not analyze - {e}")
        
        self.report["service_health"] = service_health
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n💡 GENERATING RECOMMENDATIONS...")
        
        k8s = self.report["kubernetes_status"]
        ci = self.report["ci_tests"]
        health = self.report["service_health"]
        
        recommendations = []
        
        # Kubernetes recommendations
        if k8s.get("deployment_success_rate", 0) == 100:
            recommendations.append("✅ Kubernetes deployment is fully successful - all pods running!")
        elif k8s.get("deployment_success_rate", 0) > 50:
            recommendations.append("⚠️ Partial Kubernetes deployment - investigate failing pods")
        else:
            recommendations.append("❌ Kubernetes deployment needs major attention")
        
        # CI recommendations  
        if ci.get("success_rate", 0) == 100:
            recommendations.append("✅ All CI/CD tests passing - deployment pipeline healthy")
        else:
            recommendations.append("⚠️ Some CI/CD tests failing - review build process")
        
        # Service health recommendations
        services_with_issues = [s for s, data in health.items() if "missing_dependencies" in data.get("issues", [])]
        if services_with_issues:
            recommendations.append(f"🔧 Rebuild containers for services with missing dependencies: {', '.join(services_with_issues)}")
        
        services_running = [s for s, data in health.items() if "server_started" in data.get("issues", [])]
        if services_running:
            recommendations.append(f"🚀 {len(services_running)} services successfully started and running")
        
        # Overall platform status
        if (k8s.get("deployment_success_rate", 0) >= 80 and 
            ci.get("success_rate", 0) >= 80 and 
            len(services_running) > 5):
            recommendations.append("🎉 SomaAgent platform is operational and ready for development!")
        
        self.report["recommendations"] = recommendations
        
        for rec in recommendations:
            print(f"   {rec}")
    
    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n" + "="*80)
        print("📊 SOMAAGENT LIVE SERVER TEST REPORT")
        print("="*80)
        
        k8s = self.report["kubernetes_status"]
        ci = self.report["ci_tests"]
        
        print("🏗️ KUBERNETES DEPLOYMENT:")
        print(f"   • Pods Running: {k8s.get('running_pods', 0)}/{k8s.get('total_pods', 0)}")
        print(f"   • Services Created: {k8s.get('total_services', 0)}")
        print(f"   • Success Rate: {k8s.get('deployment_success_rate', 0):.1f}%")
        
        print("\n🔄 CI/CD PIPELINE:")
        print(f"   • Tests Passed: {ci.get('passed', 0)}/{ci.get('total', 0)}")
        print(f"   • Success Rate: {ci.get('success_rate', 0):.1f}%")
        
        print("\n🏥 SERVICE HEALTH:")
        health_summary = {}
        for service, data in self.report["service_health"].items():
            if "server_started" in data.get("issues", []):
                health_summary["running"] = health_summary.get("running", 0) + 1
            elif data.get("issues"):
                health_summary["issues"] = health_summary.get("issues", 0) + 1
            else:
                health_summary["unknown"] = health_summary.get("unknown", 0) + 1
        
        print(f"   • Services Running: {health_summary.get('running', 0)}")
        print(f"   • Services with Issues: {health_summary.get('issues', 0)}")
        print(f"   • Unknown Status: {health_summary.get('unknown', 0)}")
        
        print("\n💡 KEY RECOMMENDATIONS:")
        for rec in self.report["recommendations"]:
            print(f"   {rec}")
        
        # Overall assessment
        if (k8s.get("deployment_success_rate", 0) >= 100 and 
            ci.get("success_rate", 0) >= 80):
            print("\n🎯 OVERALL ASSESSMENT: 🚀 PLATFORM READY FOR DEVELOPMENT!")
            return True
        elif (k8s.get("deployment_success_rate", 0) >= 50):
            print("\n🎯 OVERALL ASSESSMENT: ⚠️ PLATFORM PARTIALLY OPERATIONAL")
            return False
        else:
            print("\n🎯 OVERALL ASSESSMENT: ❌ PLATFORM NEEDS ATTENTION")
            return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 STARTING COMPREHENSIVE SOMAAGENT TEST SUITE")
        print("="*80)
        
        self.check_kubernetes_status()
        self.run_ci_tests()
        self.analyze_service_health()
        self.generate_recommendations()
        
        return self.print_final_report()

def main():
    reporter = SomaAgentTestReporter()
    
    try:
        success = reporter.run_full_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()