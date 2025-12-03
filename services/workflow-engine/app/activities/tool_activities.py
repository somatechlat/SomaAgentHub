"""
Tool Activities - Handles Tool execution
"""

import logging
import httpx
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

class ToolActivities:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    @activity.defn
    async def execute_tool(self, tool_spec: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on its spec"""
        tool_type = tool_spec.get("type", "http").lower()
        tool_id = tool_spec.get("id", "unknown")
        
        # Capsule Enforcement
        capsule_spec = tool_spec.get("capsule_spec")
        if capsule_spec:
            whitelist = capsule_spec.get("toolWhitelist", [])
            # Check if tool_id (or name) is in whitelist
            # Whitelist item: {"name": "...", "version": "..."}
            allowed = any(item.get("name") == tool_id for item in whitelist)
            if not allowed:
                logger.warning(f"Tool {tool_id} blocked by capsule {capsule_spec.get('metadata', {}).get('name')}")
                return {"status": "failed", "reason": "policy_violation: tool_not_whitelisted"}
        
        logger.info(f"Executing tool {tool_id} ({tool_type}) with args {arguments}")
        
        if tool_type == "http":
            return await self._execute_http_tool(tool_spec, arguments)
        elif tool_type == "native":
            return await self._execute_native_tool(tool_spec, arguments)
        else:
            raise ValueError(f"Unsupported tool type: {tool_type}")

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
