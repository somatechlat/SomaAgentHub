"""
Load testing framework using k6.

Generates k6 JavaScript test scripts for SomaAgent services.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LoadProfile(str, Enum):
    """Load test profiles."""
    
    SMOKE = "smoke"  # Light load, verify basics
    LOAD = "load"  # Normal load
    STRESS = "stress"  # High load to find breaking point
    SPIKE = "spike"  # Sudden traffic spikes
    SOAK = "soak"  # Sustained load over time


@dataclass
class LoadTest:
    """Load test definition."""
    
    name: str
    target_url: str
    profile: LoadProfile
    duration: str
    virtual_users: int
    requests_per_second: int
    description: str
    
    # Test-specific options
    headers: Dict[str, str] = None
    thresholds: Dict[str, List[str]] = None


# Pre-defined load tests
LOAD_TESTS: List[LoadTest] = [
    # Gateway API tests
    LoadTest(
        name="gateway_smoke",
        target_url="https://api.somaagent.io",
        profile=LoadProfile.SMOKE,
        duration="5m",
        virtual_users=10,
        requests_per_second=10,
        description="Smoke test for gateway API",
        thresholds={
            "http_req_duration": ["p(95)<500"],  # 95% under 500ms
            "http_req_failed": ["rate<0.01"]  # Less than 1% errors
        }
    ),
    
    LoadTest(
        name="gateway_load",
        target_url="https://api.somaagent.io",
        profile=LoadProfile.LOAD,
        duration="30m",
        virtual_users=100,
        requests_per_second=100,
        description="Normal load test for gateway",
        thresholds={
            "http_req_duration": ["p(95)<200", "p(99)<500"],
            "http_req_failed": ["rate<0.001"]  # Less than 0.1% errors
        }
    ),
    
    LoadTest(
        name="gateway_stress",
        target_url="https://api.somaagent.io",
        profile=LoadProfile.STRESS,
        duration="20m",
        virtual_users=500,
        requests_per_second=1000,
        description="Stress test to find limits",
        thresholds={
            "http_req_duration": ["p(99)<2000"],  # P99 under 2s
            "http_req_failed": ["rate<0.05"]  # Less than 5% errors
        }
    ),
    
    # SLM Service tests
    LoadTest(
        name="slm_model_routing",
        target_url="https://api.somaagent.io/v1/chat/completions",
        profile=LoadProfile.LOAD,
        duration="15m",
        virtual_users=50,
        requests_per_second=50,
        description="Load test for model routing",
        thresholds={
            "http_req_duration": ["p(95)<2000", "p(99)<5000"],
            "http_req_failed": ["rate<0.01"]
        }
    ),
    
    # Memory Gateway tests
    LoadTest(
        name="vector_search_load",
        target_url="https://api.somaagent.io/v1/memory/search",
        profile=LoadProfile.LOAD,
        duration="20m",
        virtual_users=80,
        requests_per_second=100,
        description="Vector search performance",
        thresholds={
            "http_req_duration": ["p(95)<100", "p(99)<200"],
            "http_req_failed": ["rate<0.001"]
        }
    ),
]


class K6TestGenerator:
    """Generate k6 load test scripts."""
    
    def generate_script(self, test: LoadTest) -> str:
        """
        Generate k6 JavaScript test script.
        
        Args:
            test: Load test definition
            
        Returns:
            k6 script content
        """
        # Configure stages based on profile
        stages = self._get_stages(test.profile, test.virtual_users, test.duration)
        
        # Generate thresholds
        thresholds = self._format_thresholds(test.thresholds or {})
        
        # Generate headers
        headers = self._format_headers(test.headers or {})
        
        script = f'''import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate }} from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {{
  stages: {stages},
  thresholds: {thresholds},
  noConnectionReuse: false,
  userAgent: 'k6-load-test/{test.name}',
}};

// Test data
const BASE_URL = '{test.target_url}';
const HEADERS = {headers};

export default function() {{
  // Main test logic
  const response = http.get(BASE_URL + '/health', {{
    headers: HEADERS,
    tags: {{ name: 'HealthCheck' }},
  }});
  
  // Check response
  const success = check(response, {{
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  }});
  
  errorRate.add(!success);
  
  // Think time between requests
  sleep(1);
}}

export function handleSummary(data) {{
  return {{
    'stdout': textSummary(data, {{ indent: ' ', enableColors: true }}),
    'summary.json': JSON.stringify(data),
  }};
}}
'''
        
        return script
    
    def _get_stages(
        self,
        profile: LoadProfile,
        max_vus: int,
        duration: str
    ) -> str:
        """Get load profile stages."""
        if profile == LoadProfile.SMOKE:
            stages = [
                {"duration": "2m", "target": max_vus},
                {"duration": "3m", "target": max_vus},
            ]
        
        elif profile == LoadProfile.LOAD:
            stages = [
                {"duration": "5m", "target": max_vus},
                {"duration": "20m", "target": max_vus},
                {"duration": "5m", "target": 0},
            ]
        
        elif profile == LoadProfile.STRESS:
            stages = [
                {"duration": "2m", "target": max_vus // 2},
                {"duration": "5m", "target": max_vus},
                {"duration": "10m", "target": max_vus * 2},
                {"duration": "3m", "target": 0},
            ]
        
        elif profile == LoadProfile.SPIKE:
            stages = [
                {"duration": "2m", "target": max_vus},
                {"duration": "1m", "target": max_vus * 5},  # Spike
                {"duration": "2m", "target": max_vus},
                {"duration": "1m", "target": max_vus * 5},  # Another spike
                {"duration": "2m", "target": 0},
            ]
        
        elif profile == LoadProfile.SOAK:
            stages = [
                {"duration": "5m", "target": max_vus},
                {"duration": "3h", "target": max_vus},  # Sustained load
                {"duration": "5m", "target": 0},
            ]
        
        else:
            stages = [{"duration": duration, "target": max_vus}]
        
        return str(stages).replace("'", '"')
    
    def _format_thresholds(self, thresholds: Dict[str, List[str]]) -> str:
        """Format thresholds for k6."""
        if not thresholds:
            return "{}"
        
        formatted = {}
        for metric, conditions in thresholds.items():
            formatted[metric] = conditions
        
        return str(formatted).replace("'", '"')
    
    def _format_headers(self, headers: Dict[str, str]) -> str:
        """Format headers for k6."""
        if not headers:
            return "{}"
        
        return str(headers).replace("'", '"')
    
    def generate_all_tests(self) -> Dict[str, str]:
        """
        Generate all load test scripts.
        
        Returns:
            Dict mapping test name to script content
        """
        scripts = {}
        for test in LOAD_TESTS:
            script = self.generate_script(test)
            scripts[test.name] = script
        
        return scripts
    
    def save_script(self, test: LoadTest, output_dir: str = "./load-tests"):
        """
        Save test script to file.
        
        Args:
            test: Load test definition
            output_dir: Output directory
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        script = self.generate_script(test)
        script_path = os.path.join(output_dir, f"{test.name}.js")
        
        with open(script_path, "w") as f:
            f.write(script)
        
        logger.info(f"Saved test script: {script_path}")
        return script_path


def generate_load_tests():
    """Generate all k6 load test scripts."""
    generator = K6TestGenerator()
    
    for test in LOAD_TESTS:
        generator.save_script(test, output_dir="./scripts/load-tests")
    
    logger.info(f"Generated {len(LOAD_TESTS)} load test scripts")


if __name__ == "__main__":
    generate_load_tests()
