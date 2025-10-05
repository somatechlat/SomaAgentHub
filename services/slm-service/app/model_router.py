"""
Multi-model router for intelligent LLM selection.

Routes requests to the most cost-effective model based on:
- Task complexity
- Response time requirements
- Cost constraints
- Model availability
"""

import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""
    
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL_SLM = "local"
    TOGETHER = "together"


class ModelTier(str, Enum):
    """Model capability tiers."""
    
    FLAGSHIP = "flagship"  # GPT-4, Claude 3 Opus
    ADVANCED = "advanced"  # GPT-3.5 Turbo, Claude 3 Sonnet
    EFFICIENT = "efficient"  # Local SLMs, Claude 3 Haiku
    SPECIALIZED = "specialized"  # Fine-tuned models


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    
    name: str
    provider: ModelProvider
    tier: ModelTier
    
    # Pricing (per 1M tokens)
    input_price: Decimal
    output_price: Decimal
    
    # Capabilities
    max_tokens: int
    supports_function_calling: bool
    supports_streaming: bool
    supports_vision: bool = False
    
    # Performance
    avg_latency_ms: int = 1000
    throughput_tpm: int = 10000  # tokens per minute
    
    # Availability
    enabled: bool = True
    rate_limit_rpm: int = 1000  # requests per minute


# Model registry
MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # Anthropic models
    "claude-3-opus": ModelConfig(
        name="claude-3-opus-20240229",
        provider=ModelProvider.ANTHROPIC,
        tier=ModelTier.FLAGSHIP,
        input_price=Decimal("15.00"),
        output_price=Decimal("75.00"),
        max_tokens=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        avg_latency_ms=2000,
        rate_limit_rpm=50
    ),
    "claude-3-sonnet": ModelConfig(
        name="claude-3-sonnet-20240229",
        provider=ModelProvider.ANTHROPIC,
        tier=ModelTier.ADVANCED,
        input_price=Decimal("3.00"),
        output_price=Decimal("15.00"),
        max_tokens=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        avg_latency_ms=1200
    ),
    "claude-3-haiku": ModelConfig(
        name="claude-3-haiku-20240307",
        provider=ModelProvider.ANTHROPIC,
        tier=ModelTier.EFFICIENT,
        input_price=Decimal("0.25"),
        output_price=Decimal("1.25"),
        max_tokens=200000,
        supports_function_calling=True,
        supports_streaming=True,
        avg_latency_ms=500
    ),
    
    # OpenAI models
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo-preview",
        provider=ModelProvider.OPENAI,
        tier=ModelTier.FLAGSHIP,
        input_price=Decimal("10.00"),
        output_price=Decimal("30.00"),
        max_tokens=128000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        avg_latency_ms=1800
    ),
    "gpt-3.5-turbo": ModelConfig(
        name="gpt-3.5-turbo",
        provider=ModelProvider.OPENAI,
        tier=ModelTier.ADVANCED,
        input_price=Decimal("0.50"),
        output_price=Decimal("1.50"),
        max_tokens=16000,
        supports_function_calling=True,
        supports_streaming=True,
        avg_latency_ms=800
    ),
    
    # Local SLMs
    "llama-3-8b": ModelConfig(
        name="meta-llama/Llama-3-8b",
        provider=ModelProvider.LOCAL_SLM,
        tier=ModelTier.EFFICIENT,
        input_price=Decimal("0.00"),  # Free (local)
        output_price=Decimal("0.00"),
        max_tokens=8192,
        supports_function_calling=False,
        supports_streaming=True,
        avg_latency_ms=300,
        throughput_tpm=50000
    ),
    "phi-3-mini": ModelConfig(
        name="microsoft/phi-3-mini",
        provider=ModelProvider.LOCAL_SLM,
        tier=ModelTier.EFFICIENT,
        input_price=Decimal("0.00"),
        output_price=Decimal("0.00"),
        max_tokens=4096,
        supports_function_calling=False,
        supports_streaming=True,
        avg_latency_ms=200,
        throughput_tpm=80000
    ),
}


class ModelRouter:
    """Routes requests to optimal models."""
    
    def __init__(self):
        """Initialize model router."""
        self.registry = MODEL_REGISTRY
        self.fallback_chain: List[str] = [
            "claude-3-sonnet",
            "gpt-3.5-turbo",
            "llama-3-8b"
        ]
    
    def select_model(
        self,
        prompt: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select the best model for a request.
        
        Args:
            prompt: User prompt
            requirements: Optional requirements dict with:
                - max_cost: Maximum cost in dollars
                - max_latency_ms: Maximum latency
                - min_quality: Minimum quality tier
                - requires_vision: Needs vision capability
                - requires_functions: Needs function calling
        
        Returns:
            Selected model name
        """
        requirements = requirements or {}
        
        # Estimate complexity
        complexity = self._estimate_complexity(prompt)
        
        # Filter candidates
        candidates = self._filter_candidates(requirements)
        
        # Score and rank
        scored = []
        for model_id, config in candidates.items():
            score = self._score_model(
                config,
                complexity,
                requirements
            )
            scored.append((score, model_id, config))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        
        if not scored:
            logger.warning("No suitable model found, using fallback")
            return self.fallback_chain[0]
        
        selected = scored[0][1]
        logger.info(f"Selected model: {selected} (score: {scored[0][0]:.2f})")
        return selected
    
    def _estimate_complexity(self, prompt: str) -> float:
        """
        Estimate task complexity from prompt.
        
        Args:
            prompt: User prompt
            
        Returns:
            Complexity score 0-1 (0=simple, 1=complex)
        """
        # Simple heuristics (in production, use ML model)
        complexity = 0.0
        
        # Length
        if len(prompt) > 2000:
            complexity += 0.3
        elif len(prompt) > 500:
            complexity += 0.2
        else:
            complexity += 0.1
        
        # Complexity keywords
        complex_keywords = [
            "analyze", "compare", "reasoning", "complex",
            "detailed", "comprehensive", "explain", "research"
        ]
        keyword_count = sum(1 for kw in complex_keywords if kw in prompt.lower())
        complexity += min(keyword_count * 0.15, 0.4)
        
        # Code-related
        if "```" in prompt or "code" in prompt.lower():
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _filter_candidates(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, ModelConfig]:
        """
        Filter models by requirements.
        
        Args:
            requirements: Requirement constraints
            
        Returns:
            Filtered model registry
        """
        candidates = {}
        
        for model_id, config in self.registry.items():
            if not config.enabled:
                continue
            
            # Vision requirement
            if requirements.get("requires_vision") and not config.supports_vision:
                continue
            
            # Function calling requirement
            if requirements.get("requires_functions") and not config.supports_function_calling:
                continue
            
            # Quality tier requirement
            min_quality = requirements.get("min_quality")
            if min_quality:
                tier_order = {
                    ModelTier.EFFICIENT: 0,
                    ModelTier.ADVANCED: 1,
                    ModelTier.FLAGSHIP: 2,
                    ModelTier.SPECIALIZED: 1
                }
                if tier_order.get(config.tier, 0) < tier_order.get(min_quality, 0):
                    continue
            
            candidates[model_id] = config
        
        return candidates
    
    def _score_model(
        self,
        config: ModelConfig,
        complexity: float,
        requirements: Dict[str, Any]
    ) -> float:
        """
        Score a model for the task.
        
        Args:
            config: Model configuration
            complexity: Task complexity (0-1)
            requirements: Task requirements
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        # Quality match (flagship for complex, efficient for simple)
        tier_scores = {
            ModelTier.FLAGSHIP: 1.0,
            ModelTier.ADVANCED: 0.7,
            ModelTier.EFFICIENT: 0.4,
            ModelTier.SPECIALIZED: 0.8
        }
        quality_score = tier_scores.get(config.tier, 0.5)
        
        # Penalize overkill (flagship for simple tasks)
        if complexity < 0.3 and config.tier == ModelTier.FLAGSHIP:
            quality_score *= 0.5
        # Penalize underpowered (efficient for complex tasks)
        elif complexity > 0.7 and config.tier == ModelTier.EFFICIENT:
            quality_score *= 0.3
        
        score += quality_score * 40
        
        # Cost efficiency
        max_cost = requirements.get("max_cost", 1.0)  # Default $1
        estimated_tokens = int(len(requirements.get("prompt", "")) * 0.3 + 1000)
        estimated_cost = float(
            (config.input_price * estimated_tokens / 1_000_000) +
            (config.output_price * estimated_tokens / 1_000_000)
        )
        
        if estimated_cost <= max_cost:
            cost_score = (1 - estimated_cost / max_cost) * 30
            score += cost_score
        else:
            score -= 50  # Penalty for exceeding budget
        
        # Latency
        max_latency = requirements.get("max_latency_ms", 5000)
        if config.avg_latency_ms <= max_latency:
            latency_score = (1 - config.avg_latency_ms / max_latency) * 20
            score += latency_score
        else:
            score -= 30
        
        # Local preference (no API costs)
        if config.provider == ModelProvider.LOCAL_SLM:
            score += 10
        
        return score
    
    def get_fallback(self, failed_model: str) -> Optional[str]:
        """
        Get fallback model after failure.
        
        Args:
            failed_model: Model that failed
            
        Returns:
            Fallback model name or None
        """
        try:
            idx = self.fallback_chain.index(failed_model)
            if idx + 1 < len(self.fallback_chain):
                fallback = self.fallback_chain[idx + 1]
                logger.info(f"Falling back from {failed_model} to {fallback}")
                return fallback
        except ValueError:
            pass
        
        # Not in chain, use first fallback
        return self.fallback_chain[0]
    
    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """
        Estimate cost for a request.
        
        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in dollars
        """
        config = self.registry.get(model_id)
        if not config:
            return Decimal("0")
        
        input_cost = (config.input_price * input_tokens) / 1_000_000
        output_cost = (config.output_price * output_tokens) / 1_000_000
        
        return input_cost + output_cost


# Global router instance
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create global model router."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
