"""
⚠️ WE DO NOT MOCK - Persona Synthesizer Pipeline.

Extracts persona traits from training interactions and packages them:
- Conversation analysis
- Writing style extraction
- Decision pattern detection
- Preference learning
- Persona package generation
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class PersonaTrait:
    """A single persona trait."""
    category: str  # communication_style, technical_preference, workflow_preference
    name: str
    value: Any
    confidence: float  # 0.0 - 1.0
    examples: List[str]


@dataclass
class PersonaPackage:
    """Complete persona package."""
    name: str
    version: str
    created_at: str
    traits: List[PersonaTrait]
    vocabulary: Dict[str, int]  # Word/phrase frequencies
    response_patterns: List[Dict[str, Any]]
    decision_rules: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class PersonaSynthesizer:
    """
    Analyzes training interactions and generates persona packages.
    
    Uses NLP and pattern matching to extract behavioral traits.
    """
    
    def __init__(self):
        self.conversations: List[Dict[str, Any]] = []
        self.traits: List[PersonaTrait] = []
    
    def add_conversation(
        self,
        role: str,
        messages: List[Dict[str, str]]
    ) -> None:
        """
        Add training conversation.
        
        Args:
            role: Role identifier (developer, product_manager, etc.)
            messages: List of {role, content} messages
        """
        logger.info(f"Adding conversation with {len(messages)} messages")
        
        self.conversations.append({
            "role": role,
            "messages": messages,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def analyze_communication_style(self) -> List[PersonaTrait]:
        """Analyze communication style from conversations."""
        logger.info("Analyzing communication style")
        
        traits = []
        all_messages = []
        
        # Collect all user messages
        for conv in self.conversations:
            for msg in conv["messages"]:
                if msg.get("role") == "user":
                    all_messages.append(msg["content"])
        
        if not all_messages:
            return traits
        
        # Analyze message length preference
        avg_length = sum(len(msg.split()) for msg in all_messages) / len(all_messages)
        
        if avg_length < 20:
            style = "concise"
        elif avg_length < 50:
            style = "balanced"
        else:
            style = "detailed"
        
        traits.append(PersonaTrait(
            category="communication_style",
            name="message_length_preference",
            value=style,
            confidence=0.8,
            examples=all_messages[:3]
        ))
        
        # Analyze formality
        formal_indicators = ["please", "thank you", "kindly", "would you"]
        casual_indicators = ["hey", "yeah", "cool", "awesome"]
        
        formal_count = sum(
            msg.lower().count(word)
            for msg in all_messages
            for word in formal_indicators
        )
        casual_count = sum(
            msg.lower().count(word)
            for msg in all_messages
            for word in casual_indicators
        )
        
        if formal_count > casual_count * 1.5:
            formality = "formal"
        elif casual_count > formal_count * 1.5:
            formality = "casual"
        else:
            formality = "balanced"
        
        traits.append(PersonaTrait(
            category="communication_style",
            name="formality",
            value=formality,
            confidence=0.7,
            examples=[]
        ))
        
        return traits
    
    def analyze_technical_preferences(self) -> List[PersonaTrait]:
        """Analyze technical preferences."""
        logger.info("Analyzing technical preferences")
        
        traits = []
        all_messages = []
        
        for conv in self.conversations:
            for msg in conv["messages"]:
                if msg.get("role") == "user":
                    all_messages.append(msg["content"].lower())
        
        # Programming language preferences
        languages = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "go": 0,
            "rust": 0,
            "java": 0,
        }
        
        for msg in all_messages:
            for lang in languages.keys():
                if lang in msg:
                    languages[lang] += 1
        
        preferred_langs = sorted(
            [(lang, count) for lang, count in languages.items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        if preferred_langs:
            traits.append(PersonaTrait(
                category="technical_preference",
                name="programming_languages",
                value=[lang for lang, _ in preferred_langs[:3]],
                confidence=0.9,
                examples=[]
            ))
        
        # Framework preferences
        frameworks = ["react", "vue", "angular", "django", "flask", "fastapi"]
        mentioned_frameworks = [
            fw for fw in frameworks
            if any(fw in msg for msg in all_messages)
        ]
        
        if mentioned_frameworks:
            traits.append(PersonaTrait(
                category="technical_preference",
                name="frameworks",
                value=mentioned_frameworks,
                confidence=0.8,
                examples=[]
            ))
        
        return traits
    
    def analyze_workflow_preferences(self) -> List[PersonaTrait]:
        """Analyze workflow and process preferences."""
        logger.info("Analyzing workflow preferences")
        
        traits = []
        all_messages = " ".join([
            msg["content"]
            for conv in self.conversations
            for msg in conv["messages"]
            if msg.get("role") == "user"
        ]).lower()
        
        # Testing preferences
        testing_keywords = ["test", "testing", "tdd", "unit test", "integration test"]
        testing_mentions = sum(all_messages.count(kw) for kw in testing_keywords)
        
        if testing_mentions > 3:
            traits.append(PersonaTrait(
                category="workflow_preference",
                name="testing_emphasis",
                value="high",
                confidence=0.8,
                examples=[]
            ))
        
        # Documentation preferences
        doc_keywords = ["document", "documentation", "comment", "docstring"]
        doc_mentions = sum(all_messages.count(kw) for kw in doc_keywords)
        
        if doc_mentions > 3:
            traits.append(PersonaTrait(
                category="workflow_preference",
                name="documentation_emphasis",
                value="high",
                confidence=0.8,
                examples=[]
            ))
        
        # Agile methodology
        agile_keywords = ["sprint", "scrum", "kanban", "agile", "story"]
        agile_mentions = sum(all_messages.count(kw) for kw in agile_keywords)
        
        if agile_mentions > 2:
            traits.append(PersonaTrait(
                category="workflow_preference",
                name="methodology",
                value="agile",
                confidence=0.7,
                examples=[]
            ))
        
        return traits
    
    def extract_vocabulary(self) -> Dict[str, int]:
        """Extract common vocabulary and phrases."""
        logger.info("Extracting vocabulary")
        
        vocabulary = {}
        
        for conv in self.conversations:
            for msg in conv["messages"]:
                if msg.get("role") == "user":
                    # Simple word frequency
                    words = re.findall(r'\b\w+\b', msg["content"].lower())
                    for word in words:
                        if len(word) > 3:  # Filter short words
                            vocabulary[word] = vocabulary.get(word, 0) + 1
        
        # Keep top 100 most common
        sorted_vocab = sorted(
            vocabulary.items(),
            key=lambda x: x[1],
            reverse=True
        )[:100]
        
        return dict(sorted_vocab)
    
    def extract_response_patterns(self) -> List[Dict[str, Any]]:
        """Extract common request-response patterns."""
        logger.info("Extracting response patterns")
        
        patterns = []
        
        for conv in self.conversations:
            messages = conv["messages"]
            
            # Find user-assistant pairs
            for i in range(len(messages) - 1):
                if (messages[i].get("role") == "user" and
                    messages[i + 1].get("role") == "assistant"):
                    
                    user_msg = messages[i]["content"]
                    assistant_msg = messages[i + 1]["content"]
                    
                    # Extract pattern type
                    if "?" in user_msg:
                        pattern_type = "question"
                    elif any(word in user_msg.lower() for word in ["create", "build", "make"]):
                        pattern_type = "creation_request"
                    elif any(word in user_msg.lower() for word in ["fix", "debug", "error"]):
                        pattern_type = "troubleshooting"
                    else:
                        pattern_type = "general"
                    
                    patterns.append({
                        "type": pattern_type,
                        "user_intent": user_msg[:100],  # Truncate for storage
                        "response_length": len(assistant_msg.split()),
                        "response_style": "code" if "```" in assistant_msg else "text"
                    })
        
        return patterns
    
    def generate_decision_rules(self) -> List[Dict[str, Any]]:
        """Generate decision rules from observed patterns."""
        logger.info("Generating decision rules")
        
        rules = []
        
        # Rule: Prefer specific tools based on mentions
        all_text = " ".join([
            msg["content"]
            for conv in self.conversations
            for msg in conv["messages"]
        ]).lower()
        
        if "github" in all_text and all_text.count("github") > 3:
            rules.append({
                "condition": "code_repository_needed",
                "action": "prefer_github",
                "confidence": 0.8
            })
        
        if "slack" in all_text and all_text.count("slack") > 3:
            rules.append({
                "condition": "team_communication_needed",
                "action": "prefer_slack",
                "confidence": 0.8
            })
        
        return rules
    
    def synthesize_persona(
        self,
        name: str,
        version: str = "1.0.0"
    ) -> PersonaPackage:
        """
        Generate complete persona package.
        
        Args:
            name: Persona name
            version: Version string
            
        Returns:
            PersonaPackage
        """
        logger.info(f"Synthesizing persona: {name}")
        
        # Analyze all aspects
        comm_traits = self.analyze_communication_style()
        tech_traits = self.analyze_technical_preferences()
        workflow_traits = self.analyze_workflow_preferences()
        
        all_traits = comm_traits + tech_traits + workflow_traits
        
        # Extract patterns
        vocabulary = self.extract_vocabulary()
        response_patterns = self.extract_response_patterns()
        decision_rules = self.generate_decision_rules()
        
        # Create package
        package = PersonaPackage(
            name=name,
            version=version,
            created_at=datetime.utcnow().isoformat(),
            traits=all_traits,
            vocabulary=vocabulary,
            response_patterns=response_patterns,
            decision_rules=decision_rules,
            metadata={
                "conversation_count": len(self.conversations),
                "total_messages": sum(
                    len(conv["messages"])
                    for conv in self.conversations
                ),
            }
        )
        
        logger.info(f"Persona synthesized with {len(all_traits)} traits")
        return package
    
    def save_package(
        self,
        package: PersonaPackage,
        output_path: str
    ) -> None:
        """Save persona package to JSON file."""
        logger.info(f"Saving persona package to: {output_path}")
        
        with open(output_path, "w") as f:
            json.dump(asdict(package), f, indent=2)
    
    def load_package(self, package_path: str) -> PersonaPackage:
        """Load persona package from JSON file."""
        logger.info(f"Loading persona package from: {package_path}")
        
        with open(package_path, "r") as f:
            data = json.load(f)
        
        # Reconstruct PersonaTrait objects
        data["traits"] = [
            PersonaTrait(**trait)
            for trait in data["traits"]
        ]
        
        return PersonaPackage(**data)


# Example usage
if __name__ == "__main__":
    # Create synthesizer
    synthesizer = PersonaSynthesizer()
    
    # Add training conversations
    synthesizer.add_conversation(
        role="senior_developer",
        messages=[
            {"role": "user", "content": "Can you help me refactor this Python code for better performance?"},
            {"role": "assistant", "content": "Sure! Let's optimize it with list comprehensions..."},
        ]
    )
    
    # Synthesize persona
    persona = synthesizer.synthesize_persona(
        name="senior_python_developer",
        version="1.0.0"
    )
    
    # Save package
    synthesizer.save_package(persona, "personas/senior_python_developer.json")
    
    print(f"✅ Persona synthesized with {len(persona.traits)} traits")
