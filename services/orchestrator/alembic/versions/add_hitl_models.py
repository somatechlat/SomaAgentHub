"""Add HITL models - Part 4: Human Reviewer Assignments and Decisions

Revision ID: add_hitl_models
Revises: add_all_srs_models_part3
Create Date: 2025-12-03

Adds remaining HITL models:
- HumanReviewerAssignment
- HumanDecisionRecord
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "add_hitl_models"
down_revision = "add_all_srs_models_part3"
branch_labels = None
depends_on = None


def upgrade():
    """Add HITL model tables"""

    # ========== HITL MODELS (Section 10) ==========

    # Human reviewer assignments table
    op.create_table(
        "human_reviewer_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reviewer_principal_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ASSIGNED",
                "VIEWED",
                "ACTED",
                "REASSIGNED",
                "EXPIRED",
                name="reviewerassignmentstatus",
            ),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["review_session_id"],
            ["human_review_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_principal_id"],
            ["principals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_human_reviewer_assignments_tenant_id"),
        "human_reviewer_assignments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_human_reviewer_assignments_review_session_id"),
        "human_reviewer_assignments",
        ["review_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_human_reviewer_assignments_reviewer_principal_id"),
        "human_reviewer_assignments",
        ["reviewer_principal_id"],
        unique=False,
    )

    # Human decision records table
    op.create_table(
        "human_decision_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "reviewer_principal_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "decision",
            sa.Enum("APPROVE", "REJECT", "MODIFY", "ESCALATE", name="reviewdecision"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("diff_ref", sa.Text(), nullable=True),
        sa.Column("modified_payload_ref", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["review_session_id"],
            ["human_review_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_principal_id"],
            ["principals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_human_decision_records_tenant_id"),
        "human_decision_records",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_human_decision_records_review_session_id"),
        "human_decision_records",
        ["review_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_human_decision_records_timestamp"),
        "human_decision_records",
        ["timestamp"],
        unique=False,
    )


def downgrade():
    """Remove HITL tables"""

    op.drop_table("human_decision_records")
    op.drop_table("human_reviewer_assignments")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS reviewdecision")
    op.execute("DROP TYPE IF EXISTS reviewerassignmentstatus")
