"""
Tool Activities - Handles Tool execution with SRS tracking
"""

import logging
import httpx
import uuid
from datetime import datetime
from typing import Dict, Any
from temporalio import activity
from sqlmodel import select

from services.orchestrator.app.database import get_async_session
from services.common.models.tool import ToolInvocationRecord, ToolInvocationStatus, ToolDefinition

logger = logging.getLogger(__name__)

class ToolActivities:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    @activity.defn
    async def execute_tool(self, tool_spec: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on its spec and record invocation"""
        tool_type = tool_spec.get("type", "http").lower()
        tool_identifier = tool_spec.get("id", "unknown")
        
        # Context extraction
        context = arguments.get("context", {})
        metadata = context.get("metadata", {})
        tenant_id_str = metadata.get("tenant_id")
        workflow_instance_id_str = arguments.get("workflow_instance_id") # Should be passed in arguments
        node_execution_id_str = arguments.get("node_execution_id") # Should be passed in arguments
        
        # Capsule Enforcement
        capsule_spec = tool_spec.get("capsule_spec")
        policy_decision = "ALLOWED"
        if capsule_spec:
            whitelist = capsule_spec.get("toolWhitelist", [])
            allowed = any(item.get("name") == tool_identifier for item in whitelist)
            if not allowed:
                logger.warning(f"Tool {tool_identifier} blocked by capsule {capsule_spec.get('metadata', {}).get('name')}")
                policy_decision = "DENIED"
                return {"status": "failed", "reason": "policy_violation: tool_not_whitelisted"}

        logger.info(f"Executing tool {tool_identifier} ({tool_type}) with args {arguments}")

        # 1. Record Invocation Start
        invocation_id = None
        async with get_async_session() as session:
            try:
                tenant_uuid = uuid.UUID(tenant_id_str) if tenant_id_str else None
                workflow_uuid = uuid.UUID(workflow_instance_id_str) if workflow_instance_id_str else None
                node_exec_uuid = uuid.UUID(node_execution_id_str) if node_execution_id_str else None
                
                # Try to resolve ToolDefinition
                tool_def_id = None
                try:
                    tool_def_id = uuid.UUID(tool_identifier)
                except ValueError:
                    # If identifier is not UUID, try to find by name
                    stmt = select(ToolDefinition).where(ToolDefinition.name == tool_identifier)
                    if tenant_uuid:
                        stmt = stmt.where(ToolDefinition.tenant_id == tenant_uuid)
                    result = await session.execute(stmt)
                    tool_def = result.scalars().first()
                    if tool_def:
                        tool_def_id = tool_def.id

                invocation = ToolInvocationRecord(
                    tenant_id=tenant_uuid,
                    tool_definition_id=tool_def_id,
                    workflow_instance_id=workflow_uuid,
                    node_execution_id=node_exec_uuid,
                    status=ToolInvocationStatus.RUNNING,
                    started_at=datetime.utcnow(),
                    request_payload_ref=arguments, # Storing inline for now
                    policy_decision=policy_decision
                )
                session.add(invocation)
                await session.commit()
                await session.refresh(invocation)
                invocation_id = invocation.id
            except Exception as e:
                logger.error(f"Failed to record tool invocation start: {e}")

        # 2. Execute Tool
        result = {"status": "failed", "reason": "unknown_error"}
        try:
            if tool_type == "http":
                result = await self._execute_http_tool(tool_spec, arguments)
            elif tool_type == "native":
                result = await self._execute_native_tool(tool_spec, arguments)
            else:
                raise ValueError(f"Unsupported tool type: {tool_type}")
        except Exception as e:
            result = {"status": "failed", "reason": str(e)}

        # 3. Record Invocation End
        if invocation_id:
            async with get_async_session() as session:
                try:
                    stmt = select(ToolInvocationRecord).where(ToolInvocationRecord.id == invocation_id)
                    res = await session.execute(stmt)
                    inv = res.scalar_one_or_none()
                    if inv:
                        inv.finished_at = datetime.utcnow()
                        inv.response_payload_ref = result
                        if result.get("status") == "completed":
                            inv.status = ToolInvocationStatus.SUCCEEDED
                        else:
                            inv.status = ToolInvocationStatus.FAILED
                            inv.error_details = {"reason": result.get("reason")}
                        await session.commit()
                except Exception as e:
                    logger.error(f"Failed to record tool invocation end: {e}")

        return result

    async def _execute_http_tool(self, tool_spec: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = tool_spec.get("endpoint")
        if not endpoint:
            raise ValueError("Missing endpoint for HTTP tool")
            
        method = tool_spec.get("method", "POST")
        
        try:
            response = await self.http_client.request(
                method=method,
                url=endpoint,
                json=arguments
            )
            response.raise_for_status()
            return {
                "status": "completed",
                "output": response.json(),
                "tool_id": tool_spec.get("id")
            }
        except Exception as e:
            logger.error(f"HTTP tool execution failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def _execute_native_tool(self, tool_spec: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Simple native tool registry for demo/testing
        tool_id = tool_spec.get("id")
        
        if tool_id == "calculator":
            op = arguments.get("op")
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            
            if op == "add":
                result = a + b
            elif op == "sub":
                result = a - b
            elif op == "mul":
                result = a * b
            elif op == "div":
                result = a / b if b != 0 else "error: div by zero"
            else:
                result = "unknown op"
                
            return {"status": "completed", "output": result, "tool_id": tool_id}
            
        return {"status": "failed", "reason": f"Unknown native tool: {tool_id}"}
