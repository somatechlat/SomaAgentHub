"""
Tool Service - Manages tool definitions, MCP servers, and invocations.

SRS Section 6 - Tool System
Handles tool registration, discovery, and invocation tracking.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from services.common.models.tool import (
    ToolDefinition, MCPServerDefinition, ToolInvocationRecord,
    ToolType, ToolInvocationStatus, PolicyDecision,
    ToolDefinitionCreate, MCPServerDefinitionCreate,
    ToolInvocationRecordCreate
)


class ToolService:
    """Service for managing tools and MCP servers"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Tool Definitions ==========

    async def create_tool_definition(self, tool_create: ToolDefinitionCreate) -> ToolDefinition:
        """Create a new tool definition"""
        # Check if name exists in tenant
        result = await self.db.execute(
            select(ToolDefinition).where(
                ToolDefinition.tenant_id == tool_create.tenant_id,
                ToolDefinition.name == tool_create.name,
                ToolDefinition.version == tool_create.version
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tool '{tool_create.name}' version '{tool_create.version}' already exists"
            )
            
        tool = ToolDefinition(
            tenant_id=tool_create.tenant_id,
            name=tool_create.name,
            version=tool_create.version,
            type=tool_create.type,
            description=tool_create.description,
            io_contract=tool_create.io_contract,
            risk_level=tool_create.risk_level,
            default_timeout_seconds=tool_create.default_timeout_seconds,
            metadata=tool_create.metadata
        )
        
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        return tool

    async def get_tool_definition(self, tool_id: UUID, tenant_id: UUID) -> Optional[ToolDefinition]:
        """Get a tool definition by ID"""
        result = await self.db.execute(
            select(ToolDefinition).where(
                ToolDefinition.id == tool_id,
                ToolDefinition.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def list_tool_definitions(self, tenant_id: UUID, tool_type: Optional[ToolType] = None) -> List[ToolDefinition]:
        """List all tool definitions for a tenant"""
        query = select(ToolDefinition).where(ToolDefinition.tenant_id == tenant_id)
        if tool_type:
            query = query.where(ToolDefinition.type == tool_type)
        result = await self.db.execute(query)
        return result.scalars().all()

    # ========== MCP Servers ==========

    async def create_mcp_server(self, server_create: MCPServerDefinitionCreate) -> MCPServerDefinition:
        """Register a new MCP server"""
        # Check if name exists
        result = await self.db.execute(
            select(MCPServerDefinition).where(
                MCPServerDefinition.tenant_id == server_create.tenant_id,
                MCPServerDefinition.name == server_create.name
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MCP Server '{server_create.name}' already exists"
            )
            
        server = MCPServerDefinition(
            tenant_id=server_create.tenant_id,
            name=server_create.name,
            endpoint_uri=server_create.endpoint_uri,
            auth_method=server_create.auth_method,
            available_tools=server_create.available_tools
        )
        
        self.db.add(server)
        await self.db.commit()
        await self.db.refresh(server)
        return server

    async def get_mcp_server(self, server_id: UUID, tenant_id: UUID) -> Optional[MCPServerDefinition]:
        """Get an MCP server by ID"""
        result = await self.db.execute(
            select(MCPServerDefinition).where(
                MCPServerDefinition.id == server_id,
                MCPServerDefinition.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    # ========== Tool Invocations ==========

    async def record_invocation_start(self, record_create: ToolInvocationRecordCreate) -> ToolInvocationRecord:
        """Record the start of a tool invocation"""
        # Validate tool exists
        tool = await self.get_tool_definition(record_create.tool_definition_id, record_create.tenant_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool definition {record_create.tool_definition_id} not found"
            )
            
        record = ToolInvocationRecord(
            tenant_id=record_create.tenant_id,
            tool_definition_id=record_create.tool_definition_id,
            workflow_instance_id=record_create.workflow_instance_id,
            node_execution_id=record_create.node_execution_id,
            capsule_instance_id=record_create.capsule_instance_id,
            request_payload_ref=record_create.request_payload_ref,
            request_payload_inline=record_create.request_payload_inline,
            status=ToolInvocationStatus.PENDING,
            policy_decision=record_create.policy_decision,
            guardrail_flags=record_create.guardrail_flags or {}
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_invocation_status(
        self, 
        invocation_id: UUID, 
        tenant_id: UUID, 
        status: ToolInvocationStatus,
        response_payload_ref: Optional[str] = None,
        response_payload_inline: Optional[Dict] = None,
        error_details: Optional[Dict] = None
    ) -> ToolInvocationRecord:
        """Update the status of a tool invocation (e.g., completion)"""
        result = await self.db.execute(
            select(ToolInvocationRecord).where(
                ToolInvocationRecord.id == invocation_id,
                ToolInvocationRecord.tenant_id == tenant_id
            )
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool invocation {invocation_id} not found"
            )
            
        record.status = status
        if status in [ToolInvocationStatus.SUCCEEDED, ToolInvocationStatus.FAILED, ToolInvocationStatus.CANCELLED]:
            record.finished_at = datetime.utcnow()
            
        if status == ToolInvocationStatus.RUNNING and not record.started_at:
            record.started_at = datetime.utcnow()
            
        if response_payload_ref:
            record.response_payload_ref = response_payload_ref
        if response_payload_inline:
            record.response_payload_inline = response_payload_inline
        if error_details:
            record.error_details = error_details
            
        await self.db.commit()
        await self.db.refresh(record)
        return record
