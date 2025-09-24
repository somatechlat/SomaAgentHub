"""Database utilities for benchmark results."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

metadata = MetaData()

benchmark_results = Table(
    "benchmark_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("provider", String(64), nullable=False, index=True),
    Column("model", String(128), nullable=False),
    Column("role", String(64), nullable=False),
    Column("latency_ms", Float, nullable=False),
    Column("tokens", Integer, nullable=True),
    Column("cost", Float, nullable=True),
    Column("quality", Float, nullable=True),
    Column("refusal", Float, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow, server_default=text("now()")),
)


def get_engine() -> AsyncEngine:
    cfg = get_settings()
    return create_async_engine(cfg.database_url, echo=cfg.debug)


def get_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
