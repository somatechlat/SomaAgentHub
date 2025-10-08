"""A2A integration activity for agent-to-agent messaging via Temporal child workflows."""

from __future__ import annotations

from typing import Any, Dict

from temporalio import activity

# Import core protocol components
from ..core.a2a_protocol import A2AProtocol, AgentRegistry

# Global singleton registry for the service runtime
_registry = AgentRegistry()
_protocol = A2AProtocol(_registry)


@activity.defn(name="a2a-message")
async def run_a2a_message(payload: Dict[str, Any]) -> Dict:
    """Temporal activity that sends an A2A message to a target agent.

    Expected payload keys:
        - ``target_agent_id``: ID of the recipient agent.
        - ``message``: Message string to send.
        - ``sender_id``: ID of the sending agent.
        - ``metadata`` (optional): Additional metadata dict.
    """
    target_agent_id: str = str(payload.get("target_agent_id", "")).strip()
    message: str = str(payload.get("message", "")).strip()
    sender_id: str = str(payload.get("sender_id", "")).strip()
    metadata: Dict[str, Any] = payload.get("metadata") or {}

    if not target_agent_id:
        raise ValueError("'target_agent_id' is required for A2A messaging")
    if not message:
        raise ValueError("'message' is required for A2A messaging")
    if not sender_id:
        raise ValueError("'sender_id' is required for A2A messaging")

    # Perform the send via the protocol implementation
    result = await _protocol.send_message(
        target_agent_id=target_agent_id,
        message=message,
        sender_id=sender_id,
        metadata=metadata,
    )
    # Ensure result is a dict (Temporal child workflow may return any serializable type)
    return result if isinstance(result, dict) else {"result": result}
