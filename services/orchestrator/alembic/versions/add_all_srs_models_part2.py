"""Add all SRS models - Part 2: Roles, Tools, Memory, RL, Blueprints, Observability

Revision ID: add_all_srs_models_part2
Revises: add_all_srs_models_part1
Create Date: 2025-12-03

Adds remaining ~23 tables for complete SRS implementation.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "add_all_srs_models_part2"
down_revision = "add_all_srs_models_part1"
branch_labels = None
depends_on = None


def upgrade():
    """Add remaining SRS model tables"""

    # ========== ROLE MODELS (Section 5) ==========

    # Role definitions table
    op.create_table(
        "role_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "default_persona_ref_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("expected_behavior", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["default_persona_ref_id"],
            ["external_refs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_role_definitions_tenant_id"),
        "role_definitions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_definitions_name"), "role_definitions", ["name"], unique=False
    )

    # Agent bindings table
    op.create_table(
        "agent_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "agent01_agent_ref_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "supported_task_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "supported_domains", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "default_capsule_definition_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role_definitions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent01_agent_ref_id"],
            ["external_refs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["default_capsule_definition_id"],
            ["capsule_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_bindings_tenant_id"),
        "agent_bindings",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_bindings_role_id"), "agent_bindings", ["role_id"], unique=False
    )

    # Agent session bindings table
    op.create_table(
        "agent_session_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_binding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("node_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capsule_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "somabrain_persona_ref_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "somabrain_memory_bank_ref_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "agent01_session_ref_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "CLOSED", "ERROR", name="agentsessionstatus"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent_binding_id"],
            ["agent_bindings.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["capsule_instance_id"],
            ["capsule_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["somabrain_persona_ref_id"],
            ["external_refs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["somabrain_memory_bank_ref_id"],
            ["external_refs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent01_session_ref_id"],
            ["external_refs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_session_bindings_tenant_id"),
        "agent_session_bindings",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_session_bindings_agent_binding_id"),
        "agent_session_bindings",
        ["agent_binding_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_session_bindings_workflow_instance_id"),
        "agent_session_bindings",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_session_bindings_status"),
        "agent_session_bindings",
        ["status"],
        unique=False,
    )

    # ========== NODE EXECUTION (Section 4.7) ==========

    op.create_table(
        "node_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("node_id", sa.Text(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                "SKIPPED",
                "CANCELLED",
                name="nodeexecutionstatus",
            ),
            nullable=False,
        ),
        sa.Column("input_snapshot_ref", sa.Text(), nullable=True),
        sa.Column(
            "input_snapshot_inline",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("output_snapshot_ref", sa.Text(), nullable=True),
        sa.Column(
            "output_snapshot_inline",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "agent_session_binding_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("tool_invocation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hitl_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent_session_binding_id"],
            ["agent_session_bindings.id"],
        ),
        sa.ForeignKeyConstraint(
            ["hitl_session_id"],
            ["human_review_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_node_executions_tenant_id"),
        "node_executions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_node_executions_workflow_instance_id"),
        "node_executions",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_node_executions_node_id"), "node_executions", ["node_id"], unique=False
    )
    op.create_index(
        op.f("ix_node_executions_status"), "node_executions", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_node_executions_started_at"),
        "node_executions",
        ["started_at"],
        unique=False,
    )

    # ========== TOOL MODELS (Section 6) ==========

    # Tool definitions table
    op.create_table(
        "tool_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "NATIVE", "HTTP", "MCP", "DB_QUERY", "SCRIPT", "OTHER", name="tooltype"
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "io_contract", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "risk_level",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="toolrisklevel"),
            nullable=False,
        ),
        sa.Column("default_timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tool_definitions_tenant_id"),
        "tool_definitions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tool_definitions_name"), "tool_definitions", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_tool_definitions_type"), "tool_definitions", ["type"], unique=False
    )
    op.create_index(
        op.f("ix_tool_definitions_risk_level"),
        "tool_definitions",
        ["risk_level"],
        unique=False,
    )

    # MCP server definitions table
    op.create_table(
        "mcp_server_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("endpoint_uri", sa.Text(), nullable=False),
        sa.Column(
            "auth_method",
            sa.Enum("SERVICE_ACCOUNT", "OIDC", "API_KEY", "NONE", name="authmethod"),
            nullable=False,
        ),
        sa.Column(
            "available_tools", postgresql.JSONB(astext_type=sa.Text()), nullable=False
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
        op.f("ix_mcp_server_definitions_tenant_id"),
        "mcp_server_definitions",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mcp_server_definitions_name"),
        "mcp_server_definitions",
        ["name"],
        unique=False,
    )

    # Tool invocations table
    op.create_table(
        "tool_invocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("node_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capsule_instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_payload_ref", sa.Text(), nullable=True),
        sa.Column(
            "request_payload_inline",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("response_payload_ref", sa.Text(), nullable=True),
        sa.Column(
            "response_payload_inline",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                name="toolinvocationstatus",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "policy_decision",
            sa.Enum(
                "ALLOWED", "DENIED", "SANITIZED", "REQUIRES_HITL", name="policydecision"
            ),
            nullable=False,
        ),
        sa.Column(
            "guardrail_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tool_definition_id"],
            ["tool_definitions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["node_execution_id"],
            ["node_executions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["capsule_instance_id"],
            ["capsule_instances.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tool_invocations_tenant_id"),
        "tool_invocations",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tool_invocations_tool_definition_id"),
        "tool_invocations",
        ["tool_definition_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tool_invocations_workflow_instance_id"),
        "tool_invocations",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tool_invocations_status"), "tool_invocations", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_tool_invocations_created_at"),
        "tool_invocations",
        ["created_at"],
        unique=False,
    )

    # ========== MEMORY MODELS (Section 7) ==========

    # Memory binding specs table
    op.create_table(
        "memory_binding_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "somabrain_memory_bank_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "somabrain_example_store_ref_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "write_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "read_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False
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
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["somabrain_example_store_ref_id"],
            ["external_refs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memory_binding_specs_tenant_id"),
        "memory_binding_specs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_binding_specs_task_id"),
        "memory_binding_specs",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_binding_specs_workflow_instance_id"),
        "memory_binding_specs",
        ["workflow_instance_id"],
        unique=False,
    )

    # Memory operations table
    op.create_table(
        "memory_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "workflow_instance_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("node_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "operation_type",
            sa.Enum("READ", "WRITE", "UPDATE", "DELETE", name="memoryoperationtype"),
            nullable=False,
        ),
        sa.Column("somabrain_ref_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "request_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "response_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("policy_decision", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workflow_instance_id"],
            ["workflow_instances.id"],
        ),
        sa.ForeignKeyConstraint(
            ["node_execution_id"],
            ["node_executions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["somabrain_ref_id"],
            ["external_refs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memory_operations_tenant_id"),
        "memory_operations",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_operations_workflow_instance_id"),
        "memory_operations",
        ["workflow_instance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_operations_operation_type"),
        "memory_operations",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_operations_created_at"),
        "memory_operations",
        ["created_at"],
        unique=False,
    )


def downgrade():
    """Remove part 2 tables"""

    # Drop in reverse order
    op.drop_table("memory_operations")
    op.drop_table("memory_binding_specs")
    op.drop_table("tool_invocations")
    op.drop_table("mcp_server_definitions")
    op.drop_table("tool_definitions")
    op.drop_table("node_executions")
    op.drop_table("agent_session_bindings")
    op.drop_table("agent_bindings")
    op.drop_table("role_definitions")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS memoryoperationtype")
    op.execute("DROP TYPE IF EXISTS policydecision")
    op.execute("DROP TYPE IF EXISTS toolinvocationstatus")
    op.execute("DROP TYPE IF EXISTS authmethod")
    op.execute("DROP TYPE IF EXISTS toolrisklevel")
    op.execute("DROP TYPE IF EXISTS tooltype")
    op.execute("DROP TYPE IF EXISTS nodeexecutionstatus")
    op.execute("DROP TYPE IF EXISTS agentsessionstatus")
