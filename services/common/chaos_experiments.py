"""
Chaos engineering experiments for SomaAgent.

Uses Chaos Mesh to inject faults and test resilience.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExperimentType(str, Enum):
    """Types of chaos experiments."""
    
    POD_FAILURE = "pod_failure"
    NETWORK_DELAY = "network_delay"
    NETWORK_LOSS = "network_loss"
    NETWORK_PARTITION = "network_partition"
    STRESS_CPU = "stress_cpu"
    STRESS_MEMORY = "stress_memory"
    IO_DELAY = "io_delay"
    DNS_ERROR = "dns_error"


@dataclass
class ChaosExperiment:
    """Chaos experiment definition."""
    
    name: str
    type: ExperimentType
    target_service: str
    duration: str  # e.g., "5m", "1h"
    description: str
    
    # Type-specific parameters
    params: Dict = None
    
    # Validation checks
    validation_queries: List[str] = None  # Prometheus queries to check impact


# Pre-defined chaos experiments for SomaAgent
EXPERIMENTS: List[ChaosExperiment] = [
    # Pod failures
    ChaosExperiment(
        name="gateway_pod_failure",
        type=ExperimentType.POD_FAILURE,
        target_service="gateway-api",
        duration="2m",
        description="Kill gateway-api pod to test failover",
        params={"mode": "one"},
        validation_queries=[
            'rate(http_requests_total{service="gateway-api"}[1m]) > 0',
            'up{service="gateway-api"} == 1'
        ]
    ),
    
    ChaosExperiment(
        name="slm_service_failure",
        type=ExperimentType.POD_FAILURE,
        target_service="slm-service",
        duration="3m",
        description="Kill SLM service pod to test model routing fallback",
        params={"mode": "one"},
        validation_queries=[
            'rate(model_requests_total[1m]) > 0',
            'model_fallback_total > 0'
        ]
    ),
    
    # Network chaos
    ChaosExperiment(
        name="memory_gateway_latency",
        type=ExperimentType.NETWORK_DELAY,
        target_service="memory-gateway",
        duration="5m",
        description="Add 100ms latency to memory-gateway",
        params={
            "delay": "100ms",
            "jitter": "10ms"
        },
        validation_queries=[
            'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="memory-gateway"}[1m])) < 0.5'
        ]
    ),
    
    ChaosExperiment(
        name="vector_store_packet_loss",
        type=ExperimentType.NETWORK_LOSS,
        target_service="memory-gateway",
        duration="3m",
        description="Inject 10% packet loss to vector store",
        params={
            "loss": "10",
            "correlation": "25"
        },
        validation_queries=[
            'rate(vector_search_errors_total[1m]) < 0.05'
        ]
    ),
    
    # Resource stress
    ChaosExperiment(
        name="gateway_cpu_stress",
        type=ExperimentType.STRESS_CPU,
        target_service="gateway-api",
        duration="10m",
        description="Stress gateway CPU to 80%",
        params={
            "workers": "2",
            "load": "80"
        },
        validation_queries=[
            'rate(http_requests_total{service="gateway-api",code="200"}[1m]) > 10'
        ]
    ),
    
    ChaosExperiment(
        name="slm_memory_stress",
        type=ExperimentType.STRESS_MEMORY,
        target_service="slm-service",
        duration="5m",
        description="Fill 70% of SLM service memory",
        params={
            "size": "70%"
        },
        validation_queries=[
            'container_memory_usage_bytes{pod=~"slm-service.*"} < container_spec_memory_limit_bytes'
        ]
    ),
    
    # I/O chaos
    ChaosExperiment(
        name="clickhouse_io_delay",
        type=ExperimentType.IO_DELAY,
        target_service="clickhouse",
        duration="5m",
        description="Add I/O delay to ClickHouse",
        params={
            "delay": "50ms",
            "percent": "50"
        },
        validation_queries=[
            'rate(clickhouse_query_duration_seconds[1m]) < 1.0'
        ]
    ),
]


class ChaosRunner:
    """Run chaos engineering experiments."""
    
    def __init__(self, namespace: str = "somaagent"):
        """
        Initialize chaos runner.
        
        Args:
            namespace: Kubernetes namespace
        """
        self.namespace = namespace
    
    def generate_manifest(self, experiment: ChaosExperiment) -> Dict:
        """
        Generate Chaos Mesh manifest for experiment.
        
        Args:
            experiment: Chaos experiment definition
            
        Returns:
            Kubernetes manifest
        """
        base_manifest = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "metadata": {
                "name": experiment.name,
                "namespace": self.namespace,
                "annotations": {
                    "description": experiment.description
                }
            },
            "spec": {
                "mode": experiment.params.get("mode", "all"),
                "duration": experiment.duration,
                "selector": {
                    "namespaces": [self.namespace],
                    "labelSelectors": {
                        "app": experiment.target_service
                    }
                }
            }
        }
        
        # Add experiment-specific configuration
        if experiment.type == ExperimentType.POD_FAILURE:
            base_manifest["kind"] = "PodChaos"
            base_manifest["spec"]["action"] = "pod-kill"
        
        elif experiment.type == ExperimentType.NETWORK_DELAY:
            base_manifest["kind"] = "NetworkChaos"
            base_manifest["spec"]["action"] = "delay"
            base_manifest["spec"]["delay"] = {
                "latency": experiment.params["delay"],
                "jitter": experiment.params.get("jitter", "0ms")
            }
        
        elif experiment.type == ExperimentType.NETWORK_LOSS:
            base_manifest["kind"] = "NetworkChaos"
            base_manifest["spec"]["action"] = "loss"
            base_manifest["spec"]["loss"] = {
                "loss": experiment.params["loss"],
                "correlation": experiment.params.get("correlation", "0")
            }
        
        elif experiment.type == ExperimentType.NETWORK_PARTITION:
            base_manifest["kind"] = "NetworkChaos"
            base_manifest["spec"]["action"] = "partition"
        
        elif experiment.type == ExperimentType.STRESS_CPU:
            base_manifest["kind"] = "StressChaos"
            base_manifest["spec"]["stressors"] = {
                "cpu": {
                    "workers": experiment.params["workers"],
                    "load": experiment.params["load"]
                }
            }
        
        elif experiment.type == ExperimentType.STRESS_MEMORY:
            base_manifest["kind"] = "StressChaos"
            base_manifest["spec"]["stressors"] = {
                "memory": {
                    "workers": 1,
                    "size": experiment.params["size"]
                }
            }
        
        elif experiment.type == ExperimentType.IO_DELAY:
            base_manifest["kind"] = "IOChaos"
            base_manifest["spec"]["action"] = "latency"
            base_manifest["spec"]["delay"] = experiment.params["delay"]
            base_manifest["spec"]["percent"] = experiment.params["percent"]
        
        elif experiment.type == ExperimentType.DNS_ERROR:
            base_manifest["kind"] = "DNSChaos"
            base_manifest["spec"]["action"] = "error"
        
        return base_manifest
    
    def run_experiment(self, experiment: ChaosExperiment) -> str:
        """
        Run a chaos experiment.
        
        Args:
            experiment: Experiment to run
            
        Returns:
            Experiment ID
        """
        import yaml
        import subprocess
        
        manifest = self.generate_manifest(experiment)
        manifest_yaml = yaml.dump(manifest)
        
        logger.info(f"Running chaos experiment: {experiment.name}")
        
        # Apply manifest via kubectl
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=manifest_yaml.encode(),
            capture_output=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to start experiment: {result.stderr.decode()}")
            raise RuntimeError(f"Experiment failed to start: {result.stderr.decode()}")
        
        logger.info(f"Started experiment {experiment.name} for {experiment.duration}")
        return experiment.name
    
    def stop_experiment(self, experiment_name: str):
        """
        Stop a running experiment.
        
        Args:
            experiment_name: Name of experiment to stop
        """
        import subprocess
        
        result = subprocess.run(
            [
                "kubectl", "delete",
                "podchaos,networkchaos,stresschaos,iochaos,dnschaos",
                experiment_name,
                "-n", self.namespace
            ],
            capture_output=True
        )
        
        if result.returncode == 0:
            logger.info(f"Stopped experiment: {experiment_name}")
        else:
            logger.error(f"Failed to stop experiment: {result.stderr.decode()}")
    
    def validate_experiment(
        self,
        experiment: ChaosExperiment,
        prometheus_url: str = "http://prometheus:9090"
    ) -> Dict:
        """
        Validate experiment impact using Prometheus queries.
        
        Args:
            experiment: Experiment to validate
            prometheus_url: Prometheus URL
            
        Returns:
            Validation results
        """
        import requests
        
        results = {
            "experiment": experiment.name,
            "validations": []
        }
        
        for query in (experiment.validation_queries or []):
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=5
                )
                
                data = response.json()
                is_valid = (
                    data["status"] == "success" and
                    len(data["data"]["result"]) > 0
                )
                
                results["validations"].append({
                    "query": query,
                    "valid": is_valid,
                    "result": data["data"]["result"]
                })
                
            except Exception as e:
                logger.error(f"Validation query failed: {e}")
                results["validations"].append({
                    "query": query,
                    "valid": False,
                    "error": str(e)
                })
        
        return results
