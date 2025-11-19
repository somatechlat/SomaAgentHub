"""Models for the Solver‑Verifier‑Corrector (V‑C) reasoning loop.

These tables store each *episode* (a full problem‑solving session) and the
individual *steps* performed by the Solver, Verifier, and Corrector agents.

The design mirrors the existing SQLModel usage throughout the orchestrator
service – a lightweight ORM that works with both PostgreSQL and SQLite.  The
models are deliberately simple: they capture identifiers, timestamps, role
information, input/output payloads, and a numeric reward.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON, String


class VCRole(str, Enum):
    """Roles participating in the V‑C loop."""

    SOLVER = "solver"
    VERIFIER = "verifier"
    CORRECTOR = "corrector"


class VCEpisode(SQLModel, table=True):
    """Top‑level episode representing a single reasoning problem.

    An episode groups a series of ``VCStep`` records.  The ``status`` field is
    free‑form – typical values are ``running``, ``completed`` and ``failed``.
    """

    __tablename__ = "vc_episodes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant: str = Field(index=True)
    problem: dict[str, Any] = Field(sa_column=Column(JSON))
    status: str = Field(default="running", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VCStep(SQLModel, table=True):
    """A single step inside a V‑C episode.

    ``role`` identifies which part of the loop generated the step. ``input``
    and ``output`` are stored as JSON blobs. ``reward`` is a float – ``0.0``
    for incorrect, ``1.0`` for exact matches (the simple reward function we
    provide in ``reward.py``).
    """

    __tablename__ = "vc_steps"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    episode_id: uuid.UUID = Field(foreign_key="vc_episodes.id", index=True)
    step_index: int = Field(index=True)
    role: VCRole = Field(sa_column=Column(String))
    input: dict[str, Any] = Field(sa_column=Column(JSON))
    output: dict[str, Any] = Field(sa_column=Column(JSON))
    reward: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
