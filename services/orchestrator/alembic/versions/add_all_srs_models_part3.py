"""Add all SRS models - Part 3: RL, Blueprints, Observability (FINAL)

Revision ID: add_all_srs_models_part3
Revises: add_all_srs_models_part2
Create Date: 2025-12-03

Final migration: RL/MARL, Blueprint, and Observability tables.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "add_all_srs_models_part3"
down_revision = "add_all_srs_models_part2"
branch_labels = None
depends_on = None


def upgrade():
    """Add final SRS model tables"""

    # ========== RL/MARL MODELS (Sections 8-9) ==========

    # Reasoning pipeline specs table
    op.create_table(
        "reasoning_pipeline_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pipeline_type", sa.Text(), nullable=False),
        sa.Column("stages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("max_iterations", sa.Integer(), nullable=False),
        sa.Column(
            "sampling_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reasoning_pipeline_specs_tenant_id"),
        "reasoning_pipeline_specs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reasoning_pipeline_specs_name"),
        "reasoning_pipeline_specs",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reasoning_pipeline_specs_pipeline_type"),
        "reasoning_pipeline_specs",
        ["pipeline_type"],
        unique=False,
    )

    # Game specs table
    op.create_table(
        "game_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("players", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "game_type",
            sa.Enum("TEAM", "ZERO_SUM", "GENERAL_SUM", "STACKELBERG", name="gametype"),
            nullable=False,
        ),
        sa.Column(
            "equilibrium_target",
            sa.Enum(
                "NASH", "CORRELATED", "STACKELBERG", "NONE", name="equilibriumtarget"
            ),
            nullable=False,
        ),
        sa.Column(
            "payoff_definitions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("exploitability_tolerance", sa.Float(), nullable=False),
        sa.Column(
            "capsule_constraints",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_game_specs_tenant_id"), "game_specs", ["tenant_id"], unique=False
    )
    op.create_index(op.f("ix_game_specs_name"), "game_specs", ["name"], unique=False)
    op.create_index(
        op.f("ix_game_specs_game_type"), "game_specs", ["game_type"], unique=False
    )

    # Trajectory records table
    op.create_table(
        "trajectory_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "reasoning_pipeline_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("game_spec_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capsule_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "final_outcome",
            sa.Enum(
                "CORRECT", "INCORRECT", "PARTIAL", "ABORTED", name="trajectoryoutcome"
            ),
            nullable=False,
        ),
        sa.Column("global_reward", sa.Float(), nullable=True),
        sa.Column(
            "role_returns", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("storage_ref", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reasoning_pipeline_id"],
            ["reasoning_pipeline_specs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["game_spec_id"],
            ["game_specs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["capsule_instance_id"],
            ["capsule_instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trajectory_records_tenant_id"),
        "trajectory_records",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_task_id"),
        "trajectory_records",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_workflow_instance_id"),
        "trajectory_records",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_reasoning_pipeline_id"),
        "trajectory_records",
        ["reasoning_pipeline_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_game_spec_id"),
        "trajectory_records",
        ["game_spec_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_created_at"),
        "trajectory_records",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trajectory_records_final_outcome"),
        "trajectory_records",
        ["final_outcome"],
        unique=False,
    )

    # RL export jobs table
    op.create_table(
        "rl_export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "requested_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "filter_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="rlexportstatus"),
            nullable=False,
        ),
        sa.Column("result_location", sa.Text(), nullable=True),
        sa.Column("policy_decision", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_principal_id"],
            ["principals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rl_export_jobs_tenant_id"),
        "rl_export_jobs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rl_export_jobs_status"), "rl_export_jobs", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_rl_export_jobs_created_at"),
        "rl_export_jobs",
        ["created_at"],
        unique=False,
    )

    # ========== BLUEPRINT MODELS (Section 3) ==========

    # Blueprint definitions table
    op.create_table(
        "blueprint_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ACTIVE", "DEPRECATED", name="blueprintstatus"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "supported_task_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "required_parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "optional_parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "default_capsule_definition_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("graph_template_ref", sa.Text(), nullable=True),
        sa.Column(
            "wizard_mode",
            sa.Enum("REQUIRED", "OPTIONAL", "DISABLED", name="wizardmode"),
            nullable=False,
        ),
        sa.Column(
            "constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["default_capsule_definition_id"],
            ["capsule_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_blueprint_definitions_tenant_id"),
        "blueprint_definitions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_blueprint_definitions_name"),
        "blueprint_definitions",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_blueprint_definitions_status"),
        "blueprint_definitions",
        ["status"],
        unique=False,
    )

    # Plan specs table
    op.create_table(
        "plan_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "blueprint_definition_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("blueprint_version", sa.Integer(), nullable=False),
        sa.Column(
            "parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("capsule_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "graph_workflow_definition_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "reasoning_pipelines",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_by_principal_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["blueprint_definition_id"],
            ["blueprint_definitions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["capsule_instance_id"],
            ["capsule_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["graph_workflow_definition_id"],
            ["graph_workflows.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by_principal_id"],
            ["principals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plan_specs_tenant_id"), "plan_specs", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_plan_specs_task_id"), "plan_specs", ["task_id"], unique=False
    )

    # ========== OBSERVABILITY MODELS (Section 11) ==========

    # Trace span summaries table
    op.create_table(
        "soma_trace_span_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=False),
        sa.Column("span_id", sa.Text(), nullable=False),
        sa.Column("parent_span_id", sa.Text(), nullable=True),
        sa.Column(
            "component",
            sa.Enum(
                "HUB", "AGENT01", "SOMABRAIN", "TOOL", "EXTERNAL", name="component"
            ),
            nullable=False,
        ),
        sa.Column("operation_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("OK", "ERROR", name="spanstatus"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column(
            "attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_tenant_id"),
        "soma_trace_span_summaries",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_trace_id"),
        "soma_trace_span_summaries",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_span_id"),
        "soma_trace_span_summaries",
        ["span_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_component"),
        "soma_trace_span_summaries",
        ["component"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_operation_name"),
        "soma_trace_span_summaries",
        ["operation_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_soma_trace_span_summaries_start_time"),
        "soma_trace_span_summaries",
        ["start_time"],
        unique=False,
    )

    # Evaluation scenario definitions table
    op.create_table(
        "evaluation_scenario_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "input_spec", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("expected_behavior", sa.Text(), nullable=False),
        sa.Column(
            "metrics_to_compute",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_scenario_definitions_tenant_id"),
        "evaluation_scenario_definitions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_scenario_definitions_name"),
        "evaluation_scenario_definitions",
        ["name"],
        unique=False,
    )

    # Evaluation runs table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "RUNNING", "COMPLETED", "FAILED", name="evaluationstatus"
            ),
            nullable=False,
        ),
        sa.Column(
            "evaluated_version_set",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["scenario_id"],
            ["evaluation_scenario_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_runs_tenant_id"),
        "evaluation_runs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_scenario_id"),
        "evaluation_runs",
        ["scenario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_started_at"),
        "evaluation_runs",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_runs_status"), "evaluation_runs", ["status"], unique=False
    )

    # Evaluation metric records table
    op.create_table(
        "evaluation_metric_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("details_ref", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"],
            ["evaluation_runs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_metric_records_evaluation_run_id"),
        "evaluation_metric_records",
        ["evaluation_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_metric_records_name"),
        "evaluation_metric_records",
        ["name"],
        unique=False,
    )

    # Update FKs on existing tables to point to new tables
    op.create_foreign_key(None, "tasks", "plan_specs", ["plan_spec_id"], ["id"])


def downgrade():
    """Remove part 3 tables"""

    # Drop FK first
    op.drop_constraint(None, "tasks", type_="foreignkey")

    # Drop tables in reverse order
    op.drop_table("evaluation_metric_records")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_scenario_definitions")
    op.drop_table("soma_trace_span_summaries")
    op.drop_table("plan_specs")
    op.drop_table("blueprint_definitions")
    op.drop_table("rl_export_jobs")
    op.drop_table("trajectory_records")
    op.drop_table("game_specs")
    op.drop_table("reasoning_pipeline_specs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS evaluationstatus")
    op.execute("DROP TYPE IF EXISTS spanstatus")
    op.execute("DROP TYPE IF EXISTS component")
    op.execute("DROP TYPE IF EXISTS wizardmode")
    op.execute("DROP TYPE IF EXISTS blueprintstatus")
    op.execute("DROP TYPE IF EXISTS rlexportstatus")
    op.execute("DROP TYPE IF EXISTS trajectoryoutcome")
    op.execute("DROP TYPE IF EXISTS equilibriumtarget")
    op.execute("DROP TYPE IF EXISTS gametype")
