"""Database models for MAO workflows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

metadata = MetaData()

workflows = Table(
    "mao_workflows",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(128), nullable=False),
    Column("tenant_id", String(64), nullable=False),
    Column("capsule_id", String(128), nullable=True),
    Column("status", String(32), nullable=False, server_default="pending"),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()")),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()")),
)

workflow_steps = Table(
    "mao_workflow_steps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_id", Integer, ForeignKey("mao_workflows.id", ondelete="CASCADE"), nullable=False),
    Column("step_index", Integer, nullable=False),
    Column("persona", String(128), nullable=True),
    Column("instruction", Text, nullable=False),
    Column("status", String(32), nullable=False, server_default="pending"),
    Column("result", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()")),
    Column("updated_at", DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()")),
)


cfg = get_settings()
ENGINE: AsyncEngine = create_async_engine(cfg.database_url, echo=cfg.debug)
SESSIONMAKER = async_sessionmaker(ENGINE, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    return ENGINE


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    return SESSIONMAKER


async def get_session() -> AsyncSession:
    async with SESSIONMAKER() as session:
        yield session
