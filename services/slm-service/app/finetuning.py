"""
Model fine-tuning pipeline for SomaAgent.

Supports fine-tuning OpenAI, Anthropic, and open-source models.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FineTuningProvider(str, Enum):
    """Fine-tuning providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TOGETHER = "together"
    HUGGINGFACE = "huggingface"


class FineTuningStatus(str, Enum):
    """Fine-tuning job status."""
    
    CREATED = "created"
    VALIDATING = "validating"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FineTuningJob:
    """Fine-tuning job definition."""
    
    id: str
    provider: FineTuningProvider
    base_model: str
    training_file: str
    validation_file: Optional[str]
    hyperparameters: Dict[str, Any]
    status: FineTuningStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    fine_tuned_model: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, float] = None


class FineTuningPipeline:
    """Pipeline for model fine-tuning."""
    
    def __init__(self, provider: FineTuningProvider):
        """
        Initialize fine-tuning pipeline.
        
        Args:
            provider: Fine-tuning provider
        """
        self.provider = provider
        self.client = self._init_client()
    
    def _init_client(self) -> any:
        """Initialize provider client."""
        import os
        
        if self.provider == FineTuningProvider.OPENAI:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            return openai
        
        elif self.provider == FineTuningProvider.TOGETHER:
            import together
            together.api_key = os.getenv("TOGETHER_API_KEY")
            return together
        
        elif self.provider == FineTuningProvider.HUGGINGFACE:
            from transformers import Trainer
            return Trainer
        
        return None
    
    def prepare_training_data(
        self,
        conversations: List[Dict[str, Any]],
        output_file: str
    ) -> str:
        """
        Prepare training data in provider format.
        
        Args:
            conversations: List of conversation objects
            output_file: Output file path
            
        Returns:
            Path to prepared training file
        """
        if self.provider == FineTuningProvider.OPENAI:
            # OpenAI format: JSONL with messages
            with open(output_file, 'w') as f:
                for conv in conversations:
                    training_example = {
                        "messages": [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in conv["messages"]
                        ]
                    }
                    f.write(json.dumps(training_example) + "\n")
        
        elif self.provider == FineTuningProvider.ANTHROPIC:
            # Anthropic format: JSONL with prompt/completion
            with open(output_file, 'w') as f:
                for conv in conversations:
                    # Extract user prompt and assistant response
                    user_msgs = [m["content"] for m in conv["messages"] if m["role"] == "user"]
                    assistant_msgs = [m["content"] for m in conv["messages"] if m["role"] == "assistant"]
                    
                    if user_msgs and assistant_msgs:
                        training_example = {
                            "prompt": "\n\n".join(user_msgs),
                            "completion": "\n\n".join(assistant_msgs)
                        }
                        f.write(json.dumps(training_example) + "\n")
        
        logger.info(f"Prepared {len(conversations)} training examples")
        return output_file
    
    def create_fine_tuning_job(
        self,
        base_model: str,
        training_file: str,
        validation_file: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> FineTuningJob:
        """
        Create a fine-tuning job.
        
        Args:
            base_model: Base model to fine-tune
            training_file: Path to training data
            validation_file: Path to validation data
            hyperparameters: Training hyperparameters
            
        Returns:
            Fine-tuning job
        """
        hyperparameters = hyperparameters or {}
        
        if self.provider == FineTuningProvider.OPENAI:
            # Upload training file
            with open(training_file, 'rb') as f:
                training_file_obj = self.client.File.create(
                    file=f,
                    purpose='fine-tune'
                )
            
            # Create fine-tuning job
            job = self.client.FineTuningJob.create(
                training_file=training_file_obj.id,
                model=base_model,
                hyperparameters={
                    "n_epochs": hyperparameters.get("epochs", 3),
                    "batch_size": hyperparameters.get("batch_size", 32),
                    "learning_rate_multiplier": hyperparameters.get("learning_rate", 0.1)
                }
            )
            
            return FineTuningJob(
                id=job.id,
                provider=self.provider,
                base_model=base_model,
                training_file=training_file_obj.id,
                validation_file=None,
                hyperparameters=hyperparameters,
                status=FineTuningStatus.CREATED,
                created_at=datetime.utcnow()
            )
        
        elif self.provider == FineTuningProvider.TOGETHER:
            # Together AI fine-tuning
            job = self.client.Finetune.create(
                training_file=training_file,
                model=base_model,
                n_epochs=hyperparameters.get("epochs", 3),
                learning_rate=hyperparameters.get("learning_rate", 1e-5)
            )
            
            return FineTuningJob(
                id=job.id,
                provider=self.provider,
                base_model=base_model,
                training_file=training_file,
                validation_file=validation_file,
                hyperparameters=hyperparameters,
                status=FineTuningStatus.CREATED,
                created_at=datetime.utcnow()
            )
        
        raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def get_job_status(self, job_id: str) -> FineTuningJob:
        """
        Get fine-tuning job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated job object
        """
        if self.provider == FineTuningProvider.OPENAI:
            job = self.client.FineTuningJob.retrieve(job_id)
            
            status_map = {
                "validating_files": FineTuningStatus.VALIDATING,
                "queued": FineTuningStatus.CREATED,
                "running": FineTuningStatus.RUNNING,
                "succeeded": FineTuningStatus.SUCCEEDED,
                "failed": FineTuningStatus.FAILED,
                "cancelled": FineTuningStatus.CANCELLED
            }
            
            return FineTuningJob(
                id=job.id,
                provider=self.provider,
                base_model=job.model,
                training_file=job.training_file,
                validation_file=job.validation_file,
                hyperparameters={},
                status=status_map.get(job.status, FineTuningStatus.CREATED),
                created_at=datetime.fromtimestamp(job.created_at),
                completed_at=datetime.fromtimestamp(job.finished_at) if job.finished_at else None,
                fine_tuned_model=job.fine_tuned_model,
                error=job.error.get("message") if job.error else None
            )
        
        raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def cancel_job(self, job_id: str):
        """
        Cancel a fine-tuning job.
        
        Args:
            job_id: Job ID
        """
        if self.provider == FineTuningProvider.OPENAI:
            self.client.FineTuningJob.cancel(job_id)
            logger.info(f"Cancelled job {job_id}")
        
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def list_jobs(self, limit: int = 10) -> List[FineTuningJob]:
        """
        List fine-tuning jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs
        """
        if self.provider == FineTuningProvider.OPENAI:
            jobs = self.client.FineTuningJob.list(limit=limit)
            
            return [
                FineTuningJob(
                    id=job.id,
                    provider=self.provider,
                    base_model=job.model,
                    training_file=job.training_file,
                    validation_file=job.validation_file,
                    hyperparameters={},
                    status=FineTuningStatus(job.status),
                    created_at=datetime.fromtimestamp(job.created_at),
                    fine_tuned_model=job.fine_tuned_model
                )
                for job in jobs.data
            ]
        
        return []


# Example usage
def fine_tune_from_conversations(
    conversations: List[Dict[str, Any]],
    base_model: str = "gpt-3.5-turbo",
    provider: FineTuningProvider = FineTuningProvider.OPENAI,
    epochs: int = 3
) -> FineTuningJob:
    """
    Fine-tune a model from conversation data.
    
    Args:
        conversations: Training conversations
        base_model: Base model to fine-tune
        provider: Fine-tuning provider
        epochs: Number of training epochs
        
    Returns:
        Fine-tuning job
    """
    pipeline = FineTuningPipeline(provider=provider)
    
    # Prepare training data
    training_file = "/tmp/training_data.jsonl"
    pipeline.prepare_training_data(conversations, training_file)
    
    # Create fine-tuning job
    job = pipeline.create_fine_tuning_job(
        base_model=base_model,
        training_file=training_file,
        hyperparameters={"epochs": epochs}
    )
    
    logger.info(f"Created fine-tuning job: {job.id}")
    return job
