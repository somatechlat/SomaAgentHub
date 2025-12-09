"""
RL/MARL Models - ReasoningPipelineSpec, GameSpec, TrajectoryRecord, RLExportJob

SRS Section 8 & 9 - Reasoning Pipelines and RL Export
Enables multi-agent reinforcement learning, game-theoretic equilibrium computation,
and trajectory collection for offline training.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import Base


# Enums
class GameType(str, Enum):
    """Game-theoretic configuration"""

    TEAM = "TEAM"
    ZERO_SUM = "ZERO_SUM"
    GENERAL_SUM = "GENERAL_SUM"
    STACKELBERG = "STACKELBERG"


class EquilibriumTarget(str, Enum):
    """Target equilibrium concept"""

    NASH = "NASH"
    CORRELATED = "CORRELATED"
    STACKELBERG = "STACKELBERG"
    NONE = "NONE"


class TrajectoryOutcome(str, Enum):
    """Final trajectory outcome"""

    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    PARTIAL = "PARTIAL"
    ABORTED = "ABORTED"


class RLExportStatus(str, Enum):
    """RL export job status"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Models
class ReasoningPipelineSpec(Base):
    """
    Reasoning pipeline specification for multi-role workflows.

    SRS Section 8.1 - ReasoningPipelineSpec
    Defines staged execution with multiple roles (e.g., PLANNER → SOLVER → VERIFIER).
    """

    __tablename__ = "reasoning_pipeline_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)

    # Pipeline configuration
    pipeline_type = Column(
        Text, nullable=False, index=True
    )  # e.g., "MATH_REASONING", "CODE_REVIEW"
    stages = Column(JSONB, nullable=False)  # List of PipelineStageSpec objects
    max_iterations = Column(
        Integer, nullable=False, default=10
    )  # Prevent infinite loops
    sampling_policy = Column(
        JSONB, nullable=False, default=dict
    )  # e.g., number_of_candidates for solver

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class GameSpec(Base):
    """
    Game-theoretic specification for multi-agent workflows.

    SRS Section 8.3 - GameSpec
    Enables Nash equilibrium computation and adversarial training.
    """

    __tablename__ = "game_specs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name = Column(Text, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)

    # Game configuration
    players = Column(JSONB, nullable=False)  # role_id → player label mapping
    game_type = Column(SQLEnum(GameType), nullable=False, index=True)
    equilibrium_target = Column(SQLEnum(EquilibriumTarget), nullable=False)

    # Payoff definitions (per player)
    payoff_definitions = Column(
        JSONB, nullable=False
    )  # List of PayoffDefinition objects
    exploitability_tolerance = Column(
        Float, nullable=False, default=0.01
    )  # Epsilon for approximate equilibrium

    # Capsule constraints for this game
    capsule_constraints = Column(
        JSONB, nullable=False, default=list
    )  # Required Capsule definition IDs

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class TrajectoryRecord(Base):
    """
    Complete multi-role trajectory for RL training.

    SRS Section 9.1 - TrajectoryRecord
    Stores high-level trajectory metadata; step-wise data in object store.
    """

    __tablename__ = "trajectory_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    # Context
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True
    )
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_instances.id"),
        nullable=False,
        index=True,
    )
    reasoning_pipeline_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_pipeline_specs.id"),
        nullable=True,
        index=True,
    )
    game_spec_id = Column(
        UUID(as_uuid=True), ForeignKey("game_specs.id"), nullable=True, index=True
    )
    capsule_instance_id = Column(
        UUID(as_uuid=True), ForeignKey("capsule_instances.id"), nullable=False
    )

    # Outcome
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    final_outcome = Column(SQLEnum(TrajectoryOutcome), nullable=False, index=True)

    # Rewards
    global_reward = Column(Float, nullable=True)  # Scalar global reward
    role_returns = Column(
        JSONB, nullable=False, default=dict
    )  # role_id → scalar return

    # Metadata
    meta = Column(JSONB, nullable=False, default=dict)  # difficulty, domain, tags, etc.

    # Storage reference for step-wise data
    storage_ref = Column(Text, nullable=False)  # Object store URI


class RLExportJob(Base):
    """
    RL export job for offline training.

    SRS Section 9.3 - RLExportJob
    Exports filtered trajectories for RL/MARL training.
    """

    __tablename__ = "rl_export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    requested_by_principal_id = Column(
        UUID(as_uuid=True), ForeignKey("principals.id"), nullable=False
    )

    # Filter criteria
    filter_criteria = Column(
        JSONB, nullable=False
    )  # date range, task type, Capsule, game type, difficulty

    # Status
    status = Column(
        SQLEnum(RLExportStatus),
        nullable=False,
        default=RLExportStatus.PENDING,
        index=True,
    )
    result_location = Column(
        Text, nullable=True
    )  # Object store URI of exported dataset

    # Policy decision
    policy_decision = Column(Text, nullable=True)  # OPA decision for this export

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)


# Pydantic models


class ReasoningPipelineSpecCreate(BaseModel):
    """API model for creating a reasoning pipeline spec"""

    tenant_id: PyUUID
    name: str
    version: int = 1
    description: str | None = None
    pipeline_type: str
    stages: list[dict[str, Any]]
    max_iterations: int = 10
    sampling_policy: dict[str, Any] = Field(default_factory=dict)


class ReasoningPipelineSpecResponse(BaseModel):
    """API model for reasoning pipeline spec response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    version: int
    description: str | None
    pipeline_type: str
    stages: list[dict[str, Any]]
    max_iterations: int
    sampling_policy: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameSpecCreate(BaseModel):
    """API model for creating a game spec"""

    tenant_id: PyUUID
    name: str
    version: int = 1
    description: str | None = None
    players: dict[str, str]
    game_type: GameType
    equilibrium_target: EquilibriumTarget
    payoff_definitions: list[dict[str, Any]]
    exploitability_tolerance: float = 0.01
    capsule_constraints: list[PyUUID] = Field(default_factory=list)


class GameSpecResponse(BaseModel):
    """API model for game spec response"""

    id: PyUUID
    tenant_id: PyUUID
    name: str
    version: int
    description: str | None
    players: dict[str, str]
    game_type: GameType
    equilibrium_target: EquilibriumTarget
    payoff_definitions: list[dict[str, Any]]
    exploitability_tolerance: float
    capsule_constraints: list[PyUUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrajectoryRecordCreate(BaseModel):
    """API model for creating a trajectory record"""

    tenant_id: PyUUID
    task_id: PyUUID | None = None
    workflow_instance_id: PyUUID
    reasoning_pipeline_id: PyUUID | None = None
    game_spec_id: PyUUID | None = None
    capsule_instance_id: PyUUID
    final_outcome: TrajectoryOutcome
    global_reward: float | None = None
    role_returns: dict[str, float] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)
    storage_ref: str


class TrajectoryRecordResponse(BaseModel):
    """API model for trajectory record response"""

    id: PyUUID
    tenant_id: PyUUID
    task_id: PyUUID | None
    workflow_instance_id: PyUUID
    reasoning_pipeline_id: PyUUID | None
    game_spec_id: PyUUID | None
    capsule_instance_id: PyUUID
    created_at: datetime
    final_outcome: TrajectoryOutcome
    global_reward: float | None
    role_returns: dict[str, float]
    meta: dict[str, Any]
    storage_ref: str

    class Config:
        from_attributes = True


class RLExportJobCreate(BaseModel):
    """API model for creating an RL export job"""

    tenant_id: PyUUID
    requested_by_principal_id: PyUUID
    filter_criteria: dict[str, Any]


class RLExportJobResponse(BaseModel):
    """API model for RL export job response"""

    id: PyUUID
    tenant_id: PyUUID
    requested_by_principal_id: PyUUID
    filter_criteria: dict[str, Any]
    status: RLExportStatus
    result_location: str | None
    policy_decision: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
