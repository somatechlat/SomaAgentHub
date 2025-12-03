from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from services.common.models.agent import AgentSpec, CrewSpec
from ..database import get_session
from ..models.schema import AgentModel, CrewModel

router = APIRouter(tags=["registry"])

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

@router.post("/agents", response_model=AgentSpec, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentSpec, session: AsyncSession = Depends(get_session)):
    """Register a new agent."""
    # Check if ID exists
    stmt = select(AgentModel).where(AgentModel.id == agent.id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Agent ID already exists")

    db_agent = AgentModel(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        role=agent.role,
        instructions=agent.instructions,
        tools=[t.dict(by_alias=True) for t in agent.tools],
        memory_bindings=agent.memory_bindings,
        constraints=agent.constraints.dict(by_alias=True) if agent.constraints else None,
        policy_scope=agent.policy_scope,
    )
    session.add(db_agent)
    await session.commit()
    await session.refresh(db_agent)
    return agent

@router.get("/agents/{agent_id}", response_model=AgentSpec)
async def get_agent(agent_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Get agent by ID."""
    stmt = select(AgentModel).where(AgentModel.id == agent_id)
    result = await session.execute(stmt)
    db_agent = result.scalar_one_or_none()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Map back to Pydantic
    return AgentSpec(
        id=db_agent.id,
        name=db_agent.name,
        description=db_agent.description,
        role=db_agent.role,
        instructions=db_agent.instructions,
        tools=db_agent.tools,
        memory_bindings=db_agent.memory_bindings,
        constraints=db_agent.constraints,
        policy_scope=db_agent.policy_scope,
    )

@router.put("/agents/{agent_id}", response_model=AgentSpec)
async def update_agent(agent_id: uuid.UUID, agent: AgentSpec, session: AsyncSession = Depends(get_session)):
    """Update an existing agent."""
    stmt = select(AgentModel).where(AgentModel.id == agent_id)
    result = await session.execute(stmt)
    db_agent = result.scalar_one_or_none()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_agent.name = agent.name
    db_agent.description = agent.description
    db_agent.role = agent.role
    db_agent.instructions = agent.instructions
    db_agent.tools = [t.dict(by_alias=True) for t in agent.tools]
    db_agent.memory_bindings = agent.memory_bindings
    db_agent.constraints = agent.constraints.dict(by_alias=True) if agent.constraints else None
    db_agent.policy_scope = agent.policy_scope

    await session.commit()
    await session.refresh(db_agent)
    return agent

# ---------------------------------------------------------------------------
# Crews
# ---------------------------------------------------------------------------

@router.post("/crews", response_model=CrewSpec, status_code=status.HTTP_201_CREATED)
async def create_crew(crew: CrewSpec, session: AsyncSession = Depends(get_session)):
    """Register a new crew."""
    stmt = select(CrewModel).where(CrewModel.id == crew.id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Crew ID already exists")

    db_crew = CrewModel(
        id=crew.id,
        name=crew.name,
        goal=crew.goal,
        agents=crew.agents,
        supervisor=crew.supervisor,
        routing_mode=crew.routing_mode,
    )
    session.add(db_crew)
    await session.commit()
    await session.refresh(db_crew)
    return crew

@router.get("/crews/{crew_id}", response_model=CrewSpec)
async def get_crew(crew_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Get crew by ID."""
    stmt = select(CrewModel).where(CrewModel.id == crew_id)
    result = await session.execute(stmt)
    db_crew = result.scalar_one_or_none()
    if not db_crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    
    return CrewSpec(
        id=db_crew.id,
        name=db_crew.name,
        goal=db_crew.goal,
        agents=db_crew.agents,
        supervisor=db_crew.supervisor,
        routing_mode=db_crew.routing_mode,
    )
