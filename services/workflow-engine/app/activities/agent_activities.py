"""
Agent Activities - Handles Agent execution via LLM
"""

import logging
import uuid
from typing import Dict, Any, Optional
from temporalio import activity
from sqlmodel import select

from services.orchestrator.app.database import get_async_session
from services.orchestrator.app.models.schema import AgentModel
from services.common.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

class AgentActivities:
    def __init__(self):
        self.llm_provider = OpenAIProvider()

    @activity.defn
    async def execute_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent by fetching its spec and calling LLM"""
        logger.info(f"Executing agent {agent_id} with input {input_data}")
        
        # 1. Fetch Agent Spec from DB
        async with get_async_session() as session:
            try:
                agent_uuid = uuid.UUID(agent_id)
            except ValueError:
                # If not a valid UUID, might be a system agent or mock
                logger.warning(f"Invalid UUID for agent_id: {agent_id}")
                return {"status": "failed", "reason": "invalid_agent_id"}

            stmt = select(AgentModel).where(AgentModel.id == agent_uuid)
            result = await session.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                logger.error(f"Agent not found: {agent_id}")
                return {"status": "failed", "reason": "agent_not_found"}

            # 2. Construct Prompt
            system_prompt = f"You are {agent.name}, a {agent.role}.\n"
            
            # Capsule Persona Injection
            capsule_spec = input_data.get("capsule_spec")
            if capsule_spec:
                persona_id = capsule_spec.get("personaId")
                if persona_id:
                    system_prompt += f"You are operating under the '{persona_id}' persona constraints.\n"
                    # In a real implementation, we would fetch the Persona definition from DB/Config
                    # For now, we just append the ID as a directive.
            
            if agent.description:
                system_prompt += f"Description: {agent.description}\n"
            if agent.instructions:
                system_prompt += f"Instructions: {agent.instructions}\n"
            
            user_prompt = str(input_data.get("content", input_data))

            # 3. Call LLM
            try:
                response = await self.llm_provider.complete(
                    prompt=user_prompt,
                    system_message=system_prompt,
                    model="gpt-4o" # Default to 4o for now, could be configurable in AgentSpec
                )
                
                return {
                    "status": "completed",
                    "output": response.get("completion"),
                    "usage": response.get("usage"),
                    "agent_id": agent_id
                }
                
            except Exception as e:
                logger.error(f"LLM execution failed: {e}")
                return {"status": "failed", "reason": str(e)}
