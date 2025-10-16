"""
Integration tests for SRE operations.
"""

from services.common.slo_tracker import SLOTracker, SLO
from services.common.chaos_experiments import ChaosRunner, ChaosExperiment, ExperimentType


class TestSLOTracking:
    """Test SLO tracking and monitoring."""
    
    def test_calculate_availability(self):
        """Test availability calculation."""
        tracker = SLOTracker()
        
        # Mock Prometheus response
        availability = tracker.calculate_availability(
            service="gateway-api",
            window="24h"
        )
        
        assert 0 <= availability <= 100
    
    def test_check_slo_healthy(self):
        """Test healthy SLO check."""
        tracker = SLOTracker()
        
        slo = SLO(
            name="test_slo",
            service="gateway-api",
            metric="availability",
            target=99.9,
            window="24h",
            description="Test SLO"
        )
        
        result = tracker.check_slo(slo)
        
        assert "slo" in result
        assert "status" in result
        assert result["status"] in ["healthy", "at_risk", "violated"]
    
    def test_check_all_slos(self):
        """Test checking all SLOs."""
        tracker = SLOTracker()
        
        results = tracker.check_all_slos()
        
        assert len(results) > 0
        assert all("slo" in r for r in results)
        assert all("status" in r for r in results)
    
    def test_error_budget_calculation(self):
        """Test error budget consumption."""
        tracker = SLOTracker()
        
        slo = SLO(
            name="test_availability",
            service="test-service",
            metric="availability",
            target=99.9,  # 0.1% error budget
            window="30d",
            description="Test"
        )
        
        result = tracker.check_slo(slo)
        
        # Error budget consumed should be calculated
        assert "error_budget_consumed" in result
        assert result["error_budget_consumed"] >= 0


class TestChaosEngineering:
    """Test chaos engineering framework."""
    
    def test_generate_pod_failure_manifest(self):
        """Test pod failure manifest generation."""
        runner = ChaosRunner()
        
        experiment = ChaosExperiment(
            name="test_pod_failure",
            type=ExperimentType.POD_FAILURE,
            target_service="slm-service",
            duration="1m",
            description="Test pod failure",
            params={"mode": "one"}
        )
        
        manifest = runner.generate_manifest(experiment)
        
        assert manifest["kind"] == "PodChaos"
        assert manifest["spec"]["action"] == "pod-kill"
        assert manifest["spec"]["duration"] == "1m"
    
    def test_generate_network_delay_manifest(self):
        """Test network delay manifest generation."""
        runner = ChaosRunner()
        
        experiment = ChaosExperiment(
            name="test_network_delay",
            type=ExperimentType.NETWORK_DELAY,
            target_service="slm-service",
            duration="2m",
            description="Test network delay",
            params={
                "delay": "100ms",
                "jitter": "10ms"
            }
        )
        
        manifest = runner.generate_manifest(experiment)
        
        assert manifest["kind"] == "NetworkChaos"
        assert manifest["spec"]["action"] == "delay"
        assert manifest["spec"]["delay"]["latency"] == "100ms"
    
    def test_generate_cpu_stress_manifest(self):
        """Test CPU stress manifest generation."""
        runner = ChaosRunner()
        
        experiment = ChaosExperiment(
            name="test_cpu_stress",
            type=ExperimentType.STRESS_CPU,
            target_service="memory-gateway",
            duration="5m",
            description="Test CPU stress",
            params={
                "workers": "2",
                "load": "80"
            }
        )
        
        manifest = runner.generate_manifest(experiment)
        
        assert manifest["kind"] == "StressChaos"
        assert manifest["spec"]["stressors"]["cpu"]["workers"] == "2"
        assert manifest["spec"]["stressors"]["cpu"]["load"] == "80"
    
    def test_validate_experiment(self):
        """Test experiment validation."""
        runner = ChaosRunner()
        
        experiment = ChaosExperiment(
            name="test_validation",
            type=ExperimentType.POD_FAILURE,
            target_service="gateway-api",
            duration="1m",
            description="Test",
            params={},
            validation_queries=[
                'rate(http_requests_total[1m]) > 0'
            ]
        )
        
        # This will attempt to query Prometheus
        # In tests, it should handle connection errors gracefully
        result = runner.validate_experiment(experiment)
        
        assert "experiment" in result
        assert "validations" in result


class TestLoadTesting:
    """Test load testing framework."""
    
    def test_generate_smoke_test(self):
        """Test smoke test script generation."""
        from scripts.load_testing import K6TestGenerator, LoadTest, LoadProfile
        
        generator = K6TestGenerator()
        
        test = LoadTest(
            name="test_smoke",
            target_url="https://api.test.io",
            profile=LoadProfile.SMOKE,
            duration="5m",
            virtual_users=10,
            requests_per_second=10,
            description="Test smoke"
        )
        
        script = generator.generate_script(test)
        
        assert "import http from 'k6/http'" in script
        assert "https://api.test.io" in script
        assert "stages:" in script
    
    def test_generate_load_test(self):
        """Test load test script generation."""
        from scripts.load_testing import K6TestGenerator, LoadTest, LoadProfile
        
        generator = K6TestGenerator()
        
        test = LoadTest(
            name="test_load",
            target_url="https://api.test.io",
            profile=LoadProfile.LOAD,
            duration="30m",
            virtual_users=100,
            requests_per_second=100,
            description="Test load",
            thresholds={
                "http_req_duration": ["p(95)<500"],
                "http_req_failed": ["rate<0.01"]
            }
        )
        
        script = generator.generate_script(test)
        
        assert "thresholds:" in script
        assert "http_req_duration" in script
        assert "http_req_failed" in script
    
    def test_generate_stress_test(self):
        """Test stress test script generation."""
        from scripts.load_testing import K6TestGenerator, LoadTest, LoadProfile
        
        generator = K6TestGenerator()
        
        test = LoadTest(
            name="test_stress",
            target_url="https://api.test.io",
            profile=LoadProfile.STRESS,
            duration="20m",
            virtual_users=500,
            requests_per_second=1000,
            description="Test stress"
        )
        
        script = generator.generate_script(test)
        
        # Stress test should have ramping stages
        assert "stages:" in script
        assert "target" in script
