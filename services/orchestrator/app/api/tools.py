"""
Tools API - Endpoints for managing tools and MCP servers.

SRS Section 6 - Tool System
Exposes tool definition and MCP server management via REST API.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from services.orchestrator.app.database import get_session
from services.orchestrator.app.services.tool_service import ToolService
from services.common.models.tool import (
    ToolDefinitionCreate, ToolDefinitionResponse,
    MCPServerDefinitionCreate, MCPServerDefinitionResponse,
    ToolType
)

router = APIRouter(prefix="/tools", tags=["tools"])


def get_tool_service(db: AsyncSession = Depends(get_session)) -> ToolService:
    return ToolService(db)


@router.post("/definitions", response_model=ToolDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_definition(
    tool_create: ToolDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: ToolService = Depends(get_tool_service)
):
    """Create a new tool definition"""
    if tool_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_tool_definition(tool_create)


@router.get("/definitions/{tool_id}", response_model=ToolDefinitionResponse)
async def get_tool_definition(
    tool_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: ToolService = Depends(get_tool_service)
):
    """Get a tool definition by ID"""
    tool = await service.get_tool_definition(tool_id, x_tenant_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    return tool


@router.get("/definitions", response_model=List[ToolDefinitionResponse])
async def list_tool_definitions(
    tool_type: Optional[ToolType] = Query(None),
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: ToolService = Depends(get_tool_service)
):
    """List all tool definitions for a tenant"""
    return await service.list_tool_definitions(x_tenant_id, tool_type)


@router.post("/mcp-servers", response_model=MCPServerDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_create: MCPServerDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: ToolService = Depends(get_tool_service)
):
    """Register a new MCP server"""
    if server_create.tenant_id != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID mismatch"
        )
    return await service.create_mcp_server(server_create)


@router.get("/mcp-servers/{server_id}", response_model=MCPServerDefinitionResponse)
async def get_mcp_server(
    server_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    service: ToolService = Depends(get_tool_service)
):
    """Get an MCP server by ID"""
    server = await service.get_mcp_server(server_id, x_tenant_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server {server_id} not found"
        )
    return server
