"""Database utilities for the capsule marketplace."""

from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

metadata = MetaData()

capsule_packages = Table(
    "capsule_packages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("capsule_id", String(128), nullable=False),
    Column("version", String(64), nullable=False),
    Column("owner", String(128), nullable=False),
    Column("status", String(32), nullable=False, server_default=text("'pending'")),
    Column("summary", Text, nullable=True),
    Column("attestation_hash", String(128), nullable=False),
    Column("attestation_signature", Text, nullable=True),
    Column("definition", Text, nullable=False),
    Column("compliance_report", Text, nullable=True),
    Column("tenant_scope", String(64), nullable=False, server_default=text("'global'")),
    Column("reviewer", String(128), nullable=True),
    Column("approved_at", DateTime, nullable=True),
    Column("rejected_reason", Text, nullable=True),
    Column(
        "created_at",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    ),
    Column(
        "updated_at",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    ),
    UniqueConstraint("capsule_id", "version", name="uq_capsule_packages_capsule_version"),
)

capsule_reviews = Table(
    "capsule_reviews",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "package_id",
        Integer,
        ForeignKey("capsule_packages.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("reviewer", String(128), nullable=False),
    Column("decision", String(32), nullable=False),
    Column("notes", Text, nullable=True),
    Column(
        "created_at",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    ),
    Column("is_override", Boolean, nullable=False, default=False),
)


capsule_installations = Table(
    "capsule_installations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "package_id",
        Integer,
        ForeignKey("capsule_packages.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("tenant_id", String(128), nullable=False),
    Column("environment", String(64), nullable=False, server_default=text("'prod'")),
    Column("status", String(32), nullable=False, server_default=text("'installed'")),
    Column(
        "installed_at",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    ),
    Column("installed_by", String(128), nullable=False),
    Column("notes", Text, nullable=True),
    UniqueConstraint(
        "tenant_id",
        "environment",
        "package_id",
        name="uq_capsule_installations_tenant_env_package",
    ),
)


_settings = get_settings()
_engine: AsyncEngine = create_async_engine(_settings.postgres_url, echo=False)
_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, expire_on_commit=False
)


def get_engine() -> AsyncEngine:
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _sessionmaker() as session:
        yield session


async def list_approved_packages(session: AsyncSession) -> list[dict]:
    """Return approved packages joined with latest review if available."""

    stmt = select(capsule_packages).where(capsule_packages.c.status == "approved")
    result = await session.execute(stmt)
    rows = result.mappings().all()
    return [dict(row) for row in rows]
