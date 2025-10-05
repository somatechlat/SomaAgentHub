"""
Prompt template engine with Jinja2 templates and versioning.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Environment, Template, TemplateError

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template definition."""
    
    id: str
    name: str
    template: str
    version: str
    category: str  # system, user, assistant, few_shot
    variables: List[str]
    description: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


# System prompts
SYSTEM_TEMPLATES = {
    "default_assistant": PromptTemplate(
        id="sys_default_assistant",
        name="Default Assistant",
        template=(
            "You are a helpful AI assistant. You provide accurate, thoughtful, "
            "and concise responses. If you're unsure about something, you say so."
        ),
        version="1.0",
        category="system",
        variables=[],
        description="Default system prompt for general assistant"
    ),
    
    "coding_assistant": PromptTemplate(
        id="sys_coding_assistant",
        name="Coding Assistant",
        template=(
            "You are an expert software engineer. You write clean, efficient, "
            "well-documented code. You explain your reasoning and follow best practices. "
            "Programming languages you excel at: {{ languages }}."
        ),
        version="1.0",
        category="system",
        variables=["languages"],
        description="System prompt for coding tasks"
    ),
    
    "data_analyst": PromptTemplate(
        id="sys_data_analyst",
        name="Data Analyst",
        template=(
            "You are a data analyst expert. You analyze data, create visualizations, "
            "and provide insights. You're proficient in SQL, Python (pandas, numpy), "
            "and statistical analysis."
        ),
        version="1.0",
        category="system",
        variables=[],
        description="System prompt for data analysis"
    ),
}


# User prompt templates
USER_TEMPLATES = {
    "rag_context": PromptTemplate(
        id="user_rag_context",
        name="RAG with Context",
        template=(
            "Context from knowledge base:\n"
            "{% for doc in documents %}\n"
            "---\n"
            "{{ doc.content }}\n"
            "{% endfor %}\n"
            "---\n\n"
            "Question: {{ question }}\n\n"
            "Please answer based on the context provided above."
        ),
        version="1.0",
        category="user",
        variables=["documents", "question"],
        description="RAG prompt with context injection"
    ),
    
    "few_shot_classification": PromptTemplate(
        id="user_few_shot_classification",
        name="Few-Shot Classification",
        template=(
            "Classify the following text into one of these categories: {{ categories }}.\n\n"
            "Examples:\n"
            "{% for example in examples %}\n"
            "Text: {{ example.text }}\n"
            "Category: {{ example.category }}\n\n"
            "{% endfor %}\n"
            "Now classify this:\n"
            "Text: {{ text }}\n"
            "Category:"
        ),
        version="1.0",
        category="few_shot",
        variables=["categories", "examples", "text"],
        description="Few-shot learning classification prompt"
    ),
    
    "task_execution": PromptTemplate(
        id="user_task_execution",
        name="Task Execution",
        template=(
            "Execute the following task:\n\n"
            "Task: {{ task_name }}\n"
            "Description: {{ task_description }}\n\n"
            "{% if context %}\n"
            "Context:\n{{ context }}\n\n"
            "{% endif %}\n"
            "{% if constraints %}\n"
            "Constraints:\n"
            "{% for constraint in constraints %}\n"
            "- {{ constraint }}\n"
            "{% endfor %}\n"
            "{% endif %}\n"
            "Please complete this task step by step."
        ),
        version="1.0",
        category="user",
        variables=["task_name", "task_description", "context", "constraints"],
        description="Structured task execution prompt"
    ),
}


class PromptEngine:
    """Template engine for prompts."""
    
    def __init__(self):
        """Initialize prompt engine."""
        self.env = Environment(autoescape=False)
        self.templates: Dict[str, PromptTemplate] = {}
        
        # Load default templates
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default templates."""
        self.templates.update(SYSTEM_TEMPLATES)
        self.templates.update(USER_TEMPLATES)
        logger.info(f"Loaded {len(self.templates)} default templates")
    
    def register_template(self, template: PromptTemplate):
        """
        Register a new template.
        
        Args:
            template: Template to register
        """
        self.templates[template.id] = template
        logger.debug(f"Registered template: {template.id}")
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template or None if not found
        """
        return self.templates.get(template_id)
    
    def render(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render a template with variables.
        
        Args:
            template_id: Template ID
            variables: Template variables
            
        Returns:
            Rendered prompt
        """
        template_def = self.get_template(template_id)
        if not template_def:
            raise ValueError(f"Template not found: {template_id}")
        
        try:
            template = self.env.from_string(template_def.template)
            rendered = template.render(**variables)
            
            logger.debug(f"Rendered template {template_id}")
            return rendered.strip()
            
        except TemplateError as e:
            logger.error(f"Template rendering failed: {e}")
            raise ValueError(f"Failed to render template {template_id}: {e}")
    
    def render_with_fallback(
        self,
        template_id: str,
        variables: Dict[str, Any],
        fallback: str = None
    ) -> str:
        """
        Render template with fallback on error.
        
        Args:
            template_id: Template ID
            variables: Template variables
            fallback: Fallback text if rendering fails
            
        Returns:
            Rendered prompt or fallback
        """
        try:
            return self.render(template_id, variables)
        except Exception as e:
            logger.warning(f"Template rendering failed, using fallback: {e}")
            return fallback or ""
    
    def list_templates(
        self,
        category: Optional[str] = None
    ) -> List[PromptTemplate]:
        """
        List available templates.
        
        Args:
            category: Filter by category
            
        Returns:
            List of templates
        """
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return sorted(templates, key=lambda t: t.name)
    
    def create_chain(
        self,
        templates: List[str],
        variables: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Create a prompt chain (system + user messages).
        
        Args:
            templates: List of template IDs [system_template, user_template]
            variables: Variables for all templates
            
        Returns:
            List of messages for API
        """
        messages = []
        
        for template_id in templates:
            template_def = self.get_template(template_id)
            if not template_def:
                logger.warning(f"Template not found: {template_id}")
                continue
            
            content = self.render(template_id, variables)
            
            # Map category to role
            role_map = {
                "system": "system",
                "user": "user",
                "assistant": "assistant",
                "few_shot": "user"  # Few-shot examples go as user messages
            }
            role = role_map.get(template_def.category, "user")
            
            messages.append({
                "role": role,
                "content": content
            })
        
        return messages


# Global prompt engine instance
_prompt_engine: Optional[PromptEngine] = None


def get_prompt_engine() -> PromptEngine:
    """Get or create global prompt engine."""
    global _prompt_engine
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
    return _prompt_engine
