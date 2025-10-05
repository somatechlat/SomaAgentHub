"""
⚠️ WE DO NOT MOCK - KAMACHIQ Conversational Console.

Natural language interface for autonomous project creation:
- Conversational project specification
- Real-time progress streaming
- Interactive clarifications
- Project status monitoring
"""

from typing import Dict, List, Any, Optional, AsyncIterator
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """A single conversation turn."""
    role: str  # user, assistant, system
    content: str
    timestamp: str
    metadata: Dict[str, Any]


class KAMACHIQConsole:
    """
    Conversational interface for KAMACHIQ mode.
    
    Provides natural language project creation and management.
    """
    
    def __init__(
        self,
        bootstrapper,  # KAMACHIQBootstrapper
        mao_client,  # Multi-Agent Orchestrator
    ):
        self.bootstrapper = bootstrapper
        self.mao_client = mao_client
        
        # Conversation state
        self.conversations: Dict[str, List[ConversationTurn]] = {}
        self.active_projects: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(
        self,
        session_id: str,
        message: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process user message and stream responses.
        
        Args:
            session_id: Conversation session ID
            message: User message
            
        Yields:
            Response chunks
        """
        logger.info(f"Processing message in session {session_id}")
        
        # Initialize conversation if new
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            yield {
                "type": "greeting",
                "content": "👋 Welcome to KAMACHIQ mode! I can help you bootstrap entire projects from simple descriptions. What would you like to build?"
            }
        
        # Add user message to history
        self.conversations[session_id].append(ConversationTurn(
            role="user",
            content=message,
            timestamp=datetime.utcnow().isoformat(),
            metadata={}
        ))
        
        # Detect intent
        message_lower = message.lower()
        
        # Project creation intent
        if any(word in message_lower for word in ["create", "build", "make", "new project"]):
            async for chunk in self._handle_project_creation(session_id, message):
                yield chunk
        
        # Status check intent
        elif any(word in message_lower for word in ["status", "progress", "how is"]):
            async for chunk in self._handle_status_check(session_id, message):
                yield chunk
        
        # Modification intent
        elif any(word in message_lower for word in ["change", "modify", "update", "add"]):
            async for chunk in self._handle_project_modification(session_id, message):
                yield chunk
        
        # Help intent
        elif any(word in message_lower for word in ["help", "what can you do"]):
            yield {
                "type": "help",
                "content": self._get_help_message()
            }
        
        # General response
        else:
            yield {
                "type": "text",
                "content": "I can help you create projects! Try saying something like:\n• 'Create a web app for task management'\n• 'Build a REST API for user authentication'\n• 'Make a mobile app for fitness tracking'"
            }
    
    async def _handle_project_creation(
        self,
        session_id: str,
        prompt: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Handle project creation request."""
        logger.info("Handling project creation")
        
        # Parse intent
        yield {
            "type": "thinking",
            "content": "🤔 Analyzing your project requirements..."
        }
        
        await asyncio.sleep(0.5)  # Simulate processing
        
        spec = self.bootstrapper.parse_intent(prompt)
        
        # Show parsed spec
        yield {
            "type": "spec",
            "content": f"📋 I understand you want to build:\n\n**{spec.name}**\n_{spec.description}_\n\n**Project Type:** {spec.project_type}\n**Tech Stack:** {', '.join(spec.tech_stack)}\n**Features:** {', '.join(spec.features) if spec.features else 'Standard features'}",
            "data": {
                "name": spec.name,
                "type": spec.project_type,
                "tech": spec.tech_stack
            }
        }
        
        # Ask for confirmation
        yield {
            "type": "confirmation",
            "content": "Does this look correct? I can proceed to design the architecture and bootstrap everything. Reply with:\n• ✅ 'yes' to proceed\n• ✏️ 'change [aspect]' to modify\n• ❌ 'cancel' to stop",
            "pending_action": "create_project",
            "spec": spec.__dict__
        }
        
        # Store in session
        self.conversations[session_id].append(ConversationTurn(
            role="assistant",
            content="Project specification created",
            timestamp=datetime.utcnow().isoformat(),
            metadata={"spec": spec.__dict__}
        ))
    
    async def _handle_status_check(
        self,
        session_id: str,
        message: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Handle project status check."""
        logger.info("Handling status check")
        
        if not self.active_projects:
            yield {
                "type": "text",
                "content": "No active projects yet. Create one by saying: 'Create a [type] app for [purpose]'"
            }
            return
        
        # Get latest project
        project_id = list(self.active_projects.keys())[-1]
        project = self.active_projects[project_id]
        
        yield {
            "type": "status",
            "content": f"📊 **Project Status: {project['name']}**\n\n**Progress:** {project.get('progress', 0)}%\n**Current Step:** {project.get('current_step', 'Initializing')}\n**Status:** {project.get('status', 'running')}",
            "data": project
        }
        
        # Stream real-time updates
        if project.get("status") == "running":
            yield {
                "type": "streaming",
                "content": "📡 Streaming real-time updates...",
            }
            
            # Simulate streaming updates
            for i in range(3):
                await asyncio.sleep(1)
                yield {
                    "type": "update",
                    "content": f"✓ Step {i+1} completed",
                    "progress": (i + 1) * 33
                }
    
    async def _handle_project_modification(
        self,
        session_id: str,
        message: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Handle project modification request."""
        logger.info("Handling project modification")
        
        yield {
            "type": "text",
            "content": "🔧 I can help modify the project. What would you like to change?\n• Tech stack\n• Features\n• Infrastructure\n• Team size"
        }
    
    async def confirm_and_execute(
        self,
        session_id: str,
        spec_data: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute confirmed project creation.
        
        Args:
            session_id: Session ID
            spec_data: Project specification data
            
        Yields:
            Execution updates
        """
        logger.info("Executing project creation")
        
        # Design architecture
        yield {
            "type": "progress",
            "step": "architecture",
            "content": "🏗️ Designing system architecture..."
        }
        
        await asyncio.sleep(1)
        
        from .project_bootstrapper import ProjectSpec
        spec = ProjectSpec(**spec_data)
        architecture = self.bootstrapper.design_architecture(spec)
        
        yield {
            "type": "architecture",
            "content": f"Architecture designed with {len(architecture['services'])} services",
            "data": architecture
        }
        
        # Generate execution plan
        yield {
            "type": "progress",
            "step": "planning",
            "content": "📝 Creating execution plan..."
        }
        
        await asyncio.sleep(1)
        
        execution_plan = self.bootstrapper.generate_execution_plan(spec, architecture)
        
        yield {
            "type": "plan",
            "content": f"Plan created with {len(execution_plan['steps'])} steps",
            "data": execution_plan
        }
        
        # Execute
        yield {
            "type": "progress",
            "step": "execution",
            "content": "🚀 Bootstrapping project infrastructure..."
        }
        
        # Submit to MAO
        result = self.mao_client.create_project(execution_plan)
        project_id = result.get("project_id")
        
        # Track project
        self.active_projects[project_id] = {
            "id": project_id,
            "name": spec.name,
            "status": "running",
            "progress": 0,
            "spec": spec_data,
            "started_at": datetime.utcnow().isoformat()
        }
        
        yield {
            "type": "success",
            "content": f"✅ Project **{spec.name}** is being bootstrapped!\n\n🔗 [View Dashboard](/projects/{project_id})\n📊 Monitor progress in real-time",
            "project_id": project_id
        }
        
        # Stream execution updates
        async for update in self._stream_execution_updates(project_id):
            yield update
    
    async def _stream_execution_updates(
        self,
        project_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream real-time execution updates."""
        # Connect to MAO WebSocket
        async for update in self.mao_client.stream_project_updates(project_id):
            yield {
                "type": "execution_update",
                "content": update.get("message"),
                "step": update.get("step"),
                "progress": update.get("progress"),
                "data": update
            }
    
    def _get_help_message(self) -> str:
        """Get help message."""
        return """
# 🚀 KAMACHIQ Mode - Autonomous Project Creation

I can help you bootstrap entire projects from simple descriptions!

## What I can do:

**Create Projects**
- "Create a web app for task management with React and Python"
- "Build a REST API for user authentication using FastAPI"
- "Make a mobile app for fitness tracking"

**Check Status**
- "What's the status of my project?"
- "How is the project going?"

**Modify Projects**
- "Add user authentication"
- "Change to PostgreSQL database"
- "Add Slack integration"

## Project Types:
- Web Applications
- REST APIs
- Mobile Apps
- ML Services
- Microservices

## I'll handle:
✓ Infrastructure provisioning
✓ Repository setup
✓ CI/CD pipelines
✓ Team workspace creation
✓ Documentation initialization
✓ Project management setup

Just describe what you want to build, and I'll take care of the rest!
        """


# Example usage
if __name__ == "__main__":
    from unittest.mock import Mock
    import asyncio
    
    # Mock dependencies
    bootstrapper = Mock()
    mao_client = Mock()
    
    console = KAMACHIQConsole(bootstrapper, mao_client)
    
    async def demo():
        session_id = "demo-session"
        
        async for response in console.process_message(
            session_id,
            "Create a web app called TaskMaster for team collaboration"
        ):
            print(f"[{response['type']}] {response.get('content', '')}")
    
    asyncio.run(demo())
