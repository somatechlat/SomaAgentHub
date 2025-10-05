"""
Dataset builder for fine-tuning and evaluation.

Collects high-quality training data from production conversations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger()


class DataQuality(str, Enum):
    """Data quality ratings."""
    
    EXCELLENT = "excellent"  # Perfect examples
    GOOD = "good"  # Minor issues
    FAIR = "fair"  # Needs review
    POOR = "poor"  # Not suitable


@dataclass
class TrainingExample:
    """Training example with metadata."""
    
    conversation_id: str
    messages: List[Dict[str, str]]
    quality: DataQuality
    rating: Optional[float]  # User rating if available
    task_category: str
    created_at: datetime
    metadata: Dict[str, Any]


class DatasetBuilder:
    """Build training datasets from production data."""
    
    def __init__(self, clickhouse_client):
        """
        Initialize dataset builder.
        
        Args:
            clickhouse_client: ClickHouse client for querying conversations
        """
        self.client = clickhouse_client
    
    def collect_high_quality_conversations(
        self,
        min_rating: float = 4.0,
        min_length: int = 2,
        days_back: int = 30,
        limit: int = 1000
    ) -> List[TrainingExample]:
        """
        Collect high-quality conversations for training.
        
        Args:
            min_rating: Minimum user rating (1-5)
            min_length: Minimum number of messages
            days_back: Days to look back
            limit: Maximum examples to collect
            
        Returns:
            List of training examples
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Query ClickHouse for high-quality conversations
        query = f"""
        SELECT
            conversation_id,
            messages,
            user_rating,
            task_category,
            created_at,
            metadata
        FROM conversations
        WHERE created_at >= '{cutoff_date.isoformat()}'
          AND user_rating >= {min_rating}
          AND length(messages) >= {min_length}
          AND status = 'completed'
        ORDER BY user_rating DESC, created_at DESC
        LIMIT {limit}
        """
        
        results = self.client.query(query)
        
        examples = []
        for row in results:
            quality = self._assess_quality(row)
            
            example = TrainingExample(
                conversation_id=row['conversation_id'],
                messages=row['messages'],
                quality=quality,
                rating=row['user_rating'],
                task_category=row['task_category'],
                created_at=row['created_at'],
                metadata=row['metadata']
            )
            examples.append(example)
        
        logger.info(f"Collected {len(examples)} high-quality examples")
        return examples
    
    def _assess_quality(self, conversation: Dict) -> DataQuality:
        """
        Assess conversation quality.
        
        Args:
            conversation: Conversation data
            
        Returns:
            Quality rating
        """
        rating = conversation.get('user_rating', 0)
        message_count = len(conversation.get('messages', []))
        
        # Quality heuristics
        if rating >= 4.8 and message_count >= 4:
            return DataQuality.EXCELLENT
        elif rating >= 4.0 and message_count >= 2:
            return DataQuality.GOOD
        elif rating >= 3.0:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
    
    def filter_by_task_category(
        self,
        examples: List[TrainingExample],
        categories: List[str]
    ) -> List[TrainingExample]:
        """
        Filter examples by task category.
        
        Args:
            examples: Training examples
            categories: Categories to include
            
        Returns:
            Filtered examples
        """
        filtered = [
            ex for ex in examples
            if ex.task_category in categories
        ]
        
        logger.info(f"Filtered to {len(filtered)} examples in {categories}")
        return filtered
    
    def balance_dataset(
        self,
        examples: List[TrainingExample],
        samples_per_category: int = 100
    ) -> List[TrainingExample]:
        """
        Balance dataset across categories.
        
        Args:
            examples: Training examples
            samples_per_category: Target samples per category
            
        Returns:
            Balanced dataset
        """
        from collections import defaultdict
        import random
        
        # Group by category
        by_category = defaultdict(list)
        for ex in examples:
            by_category[ex.task_category].append(ex)
        
        # Sample from each category
        balanced = []
        for category, category_examples in by_category.items():
            # Sort by quality and rating
            sorted_examples = sorted(
                category_examples,
                key=lambda x: (x.quality.value, x.rating or 0),
                reverse=True
            )
            
            # Take top N or sample if more available
            if len(sorted_examples) <= samples_per_category:
                balanced.extend(sorted_examples)
            else:
                # Take top 50%, sample rest
                top_half = sorted_examples[:samples_per_category // 2]
                rest = random.sample(
                    sorted_examples[samples_per_category // 2:],
                    samples_per_category // 2
                )
                balanced.extend(top_half + rest)
        
        logger.info(f"Balanced dataset to {len(balanced)} examples")
        return balanced
    
    def split_train_validation(
        self,
        examples: List[TrainingExample],
        validation_split: float = 0.1
    ) -> tuple:
        """
        Split dataset into training and validation.
        
        Args:
            examples: Training examples
            validation_split: Fraction for validation
            
        Returns:
            (training_examples, validation_examples)
        """
        import random
        
        # Shuffle
        shuffled = examples.copy()
        random.shuffle(shuffled)
        
        # Split
        split_idx = int(len(shuffled) * (1 - validation_split))
        training = shuffled[:split_idx]
        validation = shuffled[split_idx:]
        
        logger.info(f"Split: {len(training)} training, {len(validation)} validation")
        return training, validation
    
    def export_to_jsonl(
        self,
        examples: List[TrainingExample],
        output_file: str,
        format: str = "openai"
    ):
        """
        Export dataset to JSONL format.
        
        Args:
            examples: Training examples
            output_file: Output file path
            format: Format (openai, anthropic)
        """
        import json
        
        with open(output_file, 'w') as f:
            for example in examples:
                if format == "openai":
                    # OpenAI chat format
                    training_example = {
                        "messages": example.messages,
                        "metadata": {
                            "conversation_id": example.conversation_id,
                            "quality": example.quality.value,
                            "rating": example.rating,
                            "category": example.task_category
                        }
                    }
                
                elif format == "anthropic":
                    # Anthropic prompt/completion format
                    user_msgs = [m["content"] for m in example.messages if m["role"] == "user"]
                    assistant_msgs = [m["content"] for m in example.messages if m["role"] == "assistant"]
                    
                    training_example = {
                        "prompt": "\n\n".join(user_msgs),
                        "completion": "\n\n".join(assistant_msgs)
                    }
                
                f.write(json.dumps(training_example) + "\n")
        
        logger.info(f"Exported {len(examples)} examples to {output_file}")
    
    def generate_synthetic_examples(
        self,
        task_category: str,
        num_examples: int = 100,
        base_templates: Optional[List[Dict]] = None
    ) -> List[TrainingExample]:
        """
        Generate synthetic training examples.
        
        Args:
            task_category: Category for examples
            num_examples: Number to generate
            base_templates: Template conversations
            
        Returns:
            Synthetic training examples
        """
        import random
        
        templates = base_templates or self._get_default_templates(task_category)
        
        examples = []
        for i in range(num_examples):
            template = random.choice(templates)
            
            # Vary the template
            messages = self._vary_template(template)
            
            example = TrainingExample(
                conversation_id=f"synthetic_{task_category}_{i}",
                messages=messages,
                quality=DataQuality.GOOD,
                rating=4.0,
                task_category=task_category,
                created_at=datetime.utcnow(),
                metadata={"synthetic": True}
            )
            examples.append(example)
        
        logger.info(f"Generated {len(examples)} synthetic examples")
        return examples
    
    def _get_default_templates(self, category: str) -> List[Dict]:
        """Get default templates for category."""
        templates = {
            "code": [
                {
                    "messages": [
                        {"role": "user", "content": "Write a Python function to {task}"},
                        {"role": "assistant", "content": "Here's a Python function:\n\n```python\n{code}\n```"}
                    ]
                }
            ],
            "data": [
                {
                    "messages": [
                        {"role": "user", "content": "Analyze this dataset: {data}"},
                        {"role": "assistant", "content": "Analysis results:\n{analysis}"}
                    ]
                }
            ]
        }
        
        return templates.get(category, [])
    
    def _vary_template(self, template: Dict) -> List[Dict]:
        """Add variation to template."""
        # Simple variation - in production, use LLM to generate variations
        return template["messages"]


# Example usage
def build_training_dataset(
    clickhouse_client,
    task_categories: List[str],
    output_file: str
) -> int:
    """
    Build a training dataset from production data.
    
    Args:
        clickhouse_client: ClickHouse client
        task_categories: Categories to include
        output_file: Output file path
        
    Returns:
        Number of examples
    """
    builder = DatasetBuilder(clickhouse_client)
    
    # Collect high-quality examples
    examples = builder.collect_high_quality_conversations(
        min_rating=4.0,
        days_back=30,
        limit=5000
    )
    
    # Filter by categories
    examples = builder.filter_by_task_category(examples, task_categories)
    
    # Balance dataset
    examples = builder.balance_dataset(examples, samples_per_category=200)
    
    # Split train/val
    training, validation = builder.split_train_validation(examples)
    
    # Export
    builder.export_to_jsonl(training, output_file, format="openai")
    builder.export_to_jsonl(validation, output_file.replace(".jsonl", "_val.jsonl"), format="openai")
    
    logger.info(f"Built dataset with {len(training)} training examples")
    return len(training)
