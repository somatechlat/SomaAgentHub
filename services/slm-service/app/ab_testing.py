"""
A/B testing framework for model comparison.

Compare different models, prompts, and configurations in production.
"""

import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment status."""
    
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExperimentVariant:
    """A/B test variant."""
    
    id: str
    name: str
    model: str
    prompt_template: Optional[str]
    config: Dict[str, Any]
    traffic_allocation: float  # Percentage (0-100)
    
    # Metrics
    total_requests: int = 0
    successful_requests: int = 0
    avg_latency: float = 0.0
    avg_cost: float = 0.0
    avg_rating: float = 0.0


@dataclass
class ABExperiment:
    """A/B testing experiment."""
    
    id: str
    name: str
    description: str
    variants: List[ExperimentVariant]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Experiment config
    target_sample_size: int = 1000
    success_metric: str = "rating"  # rating, latency, cost
    min_confidence: float = 0.95


class ABTestingFramework:
    """Framework for A/B testing models and prompts."""
    
    def __init__(self, clickhouse_client):
        """
        Initialize A/B testing framework.
        
        Args:
            clickhouse_client: ClickHouse client for metrics
        """
        self.client = clickhouse_client
        self.experiments: Dict[str, ABExperiment] = {}
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[ExperimentVariant],
        target_sample_size: int = 1000
    ) -> ABExperiment:
        """
        Create a new A/B test experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            variants: Test variants
            target_sample_size: Target number of samples
            
        Returns:
            Created experiment
        """
        # Validate traffic allocation
        total_allocation = sum(v.traffic_allocation for v in variants)
        if abs(total_allocation - 100.0) > 0.01:
            raise ValueError(f"Traffic allocation must sum to 100%, got {total_allocation}%")
        
        experiment = ABExperiment(
            id=f"exp_{datetime.utcnow().timestamp()}",
            name=name,
            description=description,
            variants=variants,
            status=ExperimentStatus.DRAFT,
            created_at=datetime.utcnow(),
            target_sample_size=target_sample_size
        )
        
        self.experiments[experiment.id] = experiment
        logger.info(f"Created experiment: {experiment.id}")
        return experiment
    
    def start_experiment(self, experiment_id: str):
        """
        Start an A/B test experiment.
        
        Args:
            experiment_id: Experiment ID
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
        
        logger.info(f"Started experiment: {experiment.name}")
    
    def select_variant(self, experiment_id: str) -> ExperimentVariant:
        """
        Select a variant based on traffic allocation.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Selected variant
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            # Return default if no active experiment
            return None
        
        # Weighted random selection
        rand = random.random() * 100
        cumulative = 0
        
        for variant in experiment.variants:
            cumulative += variant.traffic_allocation
            if rand <= cumulative:
                return variant
        
        # Fallback to first variant
        return experiment.variants[0]
    
    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        latency: float,
        cost: float,
        rating: Optional[float] = None,
        success: bool = True
    ):
        """
        Record experiment result.
        
        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            latency: Response latency (ms)
            cost: Request cost ($)
            rating: User rating (1-5)
            success: Whether request succeeded
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        # Find variant
        variant = next((v for v in experiment.variants if v.id == variant_id), None)
        if not variant:
            return
        
        # Update metrics (running average)
        n = variant.total_requests
        variant.total_requests += 1
        
        if success:
            variant.successful_requests += 1
        
        # Update running averages
        variant.avg_latency = (variant.avg_latency * n + latency) / (n + 1)
        variant.avg_cost = (variant.avg_cost * n + cost) / (n + 1)
        
        if rating is not None:
            if variant.avg_rating == 0:
                variant.avg_rating = rating
            else:
                variant.avg_rating = (variant.avg_rating * n + rating) / (n + 1)
        
        # Store in ClickHouse
        self._store_result(experiment_id, variant_id, latency, cost, rating, success)
        
        # Check if experiment complete
        if variant.total_requests >= experiment.target_sample_size:
            self._check_completion(experiment_id)
    
    def _store_result(
        self,
        experiment_id: str,
        variant_id: str,
        latency: float,
        cost: float,
        rating: Optional[float],
        success: bool
    ):
        """Store result in ClickHouse."""
        query = """
        INSERT INTO ab_test_results
        (experiment_id, variant_id, latency_ms, cost_usd, user_rating, success, timestamp)
        VALUES
        """
        
        values = (
            experiment_id,
            variant_id,
            latency,
            cost,
            rating or 0,
            1 if success else 0,
            datetime.utcnow().isoformat()
        )
        
        self.client.execute(query, [values])
    
    def _check_completion(self, experiment_id: str):
        """Check if experiment has enough data."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        # Check if all variants have enough samples
        all_complete = all(
            v.total_requests >= experiment.target_sample_size
            for v in experiment.variants
        )
        
        if all_complete:
            experiment.status = ExperimentStatus.COMPLETED
            experiment.completed_at = datetime.utcnow()
            logger.info(f"Experiment completed: {experiment.name}")
    
    def analyze_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Analyze experiment results.
        
        Args:
            experiment_id: Experiment ID
            
        Returns:
            Analysis results with statistical significance
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        # Get detailed metrics from ClickHouse
        query = f"""
        SELECT
            variant_id,
            count(*) as total_requests,
            avg(latency_ms) as avg_latency,
            avg(cost_usd) as avg_cost,
            avg(user_rating) as avg_rating,
            sum(success) / count(*) as success_rate
        FROM ab_test_results
        WHERE experiment_id = '{experiment_id}'
        GROUP BY variant_id
        """
        
        results = self.client.query(query)
        
        # Calculate statistical significance
        winner = self._determine_winner(experiment, results)
        
        return {
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "status": experiment.status.value,
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "model": v.model,
                    "total_requests": v.total_requests,
                    "success_rate": v.successful_requests / v.total_requests if v.total_requests > 0 else 0,
                    "avg_latency": v.avg_latency,
                    "avg_cost": v.avg_cost,
                    "avg_rating": v.avg_rating
                }
                for v in experiment.variants
            ],
            "winner": winner,
            "started_at": experiment.started_at.isoformat() if experiment.started_at else None,
            "completed_at": experiment.completed_at.isoformat() if experiment.completed_at else None
        }
    
    def _determine_winner(
        self,
        experiment: ABExperiment,
        results: List[Dict]
    ) -> Optional[Dict]:
        """Determine winning variant with statistical significance."""
        if not results or len(results) < 2:
            return None
        
        # Sort by success metric
        metric_key = {
            "rating": "avg_rating",
            "latency": "avg_latency",
            "cost": "avg_cost"
        }.get(experiment.success_metric, "avg_rating")
        
        sorted_results = sorted(
            results,
            key=lambda x: x[metric_key],
            reverse=(experiment.success_metric == "rating")  # Higher is better for rating
        )
        
        winner = sorted_results[0]
        runner_up = sorted_results[1]
        
        # Calculate improvement
        improvement = abs(
            (winner[metric_key] - runner_up[metric_key]) / runner_up[metric_key] * 100
        )
        
        return {
            "variant_id": winner["variant_id"],
            "metric": experiment.success_metric,
            "value": winner[metric_key],
            "improvement_pct": improvement,
            "is_significant": improvement > 5  # Simple threshold
        }


# Pre-defined experiments
def create_model_comparison_experiment(
    framework: ABTestingFramework
) -> ABExperiment:
    """Create experiment comparing Claude vs GPT-4."""
    variants = [
        ExperimentVariant(
            id="claude_sonnet",
            name="Claude 3 Sonnet",
            model="claude-3-sonnet-20240229",
            prompt_template="sys_default_assistant",
            config={"temperature": 0.7},
            traffic_allocation=50.0
        ),
        ExperimentVariant(
            id="gpt4_turbo",
            name="GPT-4 Turbo",
            model="gpt-4-turbo-preview",
            prompt_template="sys_default_assistant",
            config={"temperature": 0.7},
            traffic_allocation=50.0
        )
    ]
    
    return framework.create_experiment(
        name="Claude vs GPT-4 Comparison",
        description="Compare response quality and cost between Claude 3 Sonnet and GPT-4 Turbo",
        variants=variants,
        target_sample_size=1000
    )
