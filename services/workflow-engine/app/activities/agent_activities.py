"""
Agent Activities - Handles Agent execution via Role System
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from temporalio import activity
from sqlmodel import select
from sqlalchemy.orm import selectinload

from services.orchestrator.app.database import get_async_session
from services.common.models.role import (
    RoleDefinition,
    AgentBinding,
    AgentSessionBinding,
    AgentSessionStatus,
)
from services.common.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class AgentActivities:
    def __init__(self):
        self.llm_provider = OpenAIProvider()

    @activity.defn
    async def execute_agent(
        self, role_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an agent role by resolving its binding and calling LLM"""
        logger.info(f"Executing role {role_id} with input {input_data}")

        tenant_id_str = input_data.get("tenant_id")
        if not tenant_id_str:
            # Fallback or error? For now, log warning.
            logger.warning("No tenant_id provided in input_data")
            # In real prod, might raise error.

        workflow_instance_id = input_data.get("workflow_instance_id")
        node_execution_id = input_data.get("node_execution_id")

        async with get_async_session() as session:
            try:
                role_uuid = uuid.UUID(role_id)
                tenant_uuid = uuid.UUID(tenant_id_str) if tenant_id_str else None
            except ValueError:
                logger.warning(f"Invalid UUID for role_id: {role_id}")
                return {"status": "failed", "reason": "invalid_role_id"}

            # 1. Fetch Role Definition
            stmt = select(RoleDefinition).where(RoleDefinition.id == role_uuid)
            if tenant_uuid:
                stmt = stmt.where(RoleDefinition.tenant_id == tenant_uuid)

            result = await session.execute(stmt)
            role_def = result.scalar_one_or_none()

            if not role_def:
                logger.error(f"Role not found: {role_id}")
                return {"status": "failed", "reason": "role_not_found"}

            # 2. Resolve Agent Binding
            # For now, pick the first available binding for this role.
            # In future, use a sophisticated resolution strategy based on constraints.
            binding_stmt = select(AgentBinding).where(AgentBinding.role_id == role_uuid)
            if tenant_uuid:
                binding_stmt = binding_stmt.where(AgentBinding.tenant_id == tenant_uuid)

            binding_result = await session.execute(binding_stmt)
            binding = binding_result.scalars().first()

            if not binding:
                logger.error(f"No agent binding found for role: {role_id}")
                return {"status": "failed", "reason": "no_agent_binding"}

            # 3. Create Agent Session Binding
            session_binding = AgentSessionBinding(
                tenant_id=tenant_uuid,
                agent_binding_id=binding.id,
                workflow_instance_id=(
                    uuid.UUID(workflow_instance_id) if workflow_instance_id else None
                ),
                node_execution_id=(
                    uuid.UUID(node_execution_id) if node_execution_id else None
                ),
                status=AgentSessionStatus.OPEN,
            )
            session.add(session_binding)
            await session.commit()
            await session.refresh(session_binding)

            try:
                # 4. Construct Prompt
                system_prompt = f"You are playing the role of '{role_def.name}'.\n"
                if role_def.description:
                    system_prompt += f"Description: {role_def.description}\n"

                if role_def.expected_behavior:
                    system_prompt += (
                        f"Expected Behavior: {role_def.expected_behavior}\n"
                    )

                # Capsule Persona Injection
                capsule_spec = input_data.get("capsule_spec")
                if capsule_spec:
                    persona_id = capsule_spec.get("personaId")
                    if persona_id:
                        system_prompt += f"You are operating under the '{persona_id}' persona constraints.\n"

                user_prompt = str(input_data.get("content", input_data))

                # 5. Call LLM (Simulating Agent01 execution)
                # In full implementation, this would call the Agent01 service via binding.agent01_agent_ref_id
                response = await self.llm_provider.complete(
                    prompt=user_prompt, system_message=system_prompt, model="gpt-4o"
                )

                output = response.get("completion")
                usage = response.get("usage")

                # 6. Close Session
                session_binding.status = AgentSessionStatus.CLOSED
                session_binding.closed_at = datetime.utcnow()
                await session.commit()

                return {
                    "status": "completed",
                    "output": output,
                    "usage": usage,
                    "role_id": role_id,
                    "binding_id": str(binding.id),
                    "session_id": str(session_binding.id),
                }

            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                session_binding.status = AgentSessionStatus.FAILED
                await session.commit()
                return {"status": "failed", "reason": str(e)}
