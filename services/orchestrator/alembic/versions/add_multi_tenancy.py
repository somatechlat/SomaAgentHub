"""Initial schema with multi-tenancy support

Revision ID: add_multi_tenancy
Revises: 
Create Date: 2025-12-03

Creates legacy tables with tenant_id included:
- agents
- crews
- graph_workflows
- workflow_instances
- workflow_checkpoints
- human_review_sessions
- audit_log
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_multi_tenancy'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial schema with tenant_id"""
    
    # Agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('instructions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tools', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('memory_bindings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('policy_scope', sa.Text(), nullable=True),
        sa.Column('agent_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)

    # Crews table
    op.create_table('crews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('agents', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('supervisor', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('routing_mode', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crews_tenant_id'), 'crews', ['tenant_id'], unique=False)

    # Graph Workflows table
    op.create_table('graph_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_graph_workflows_tenant_id'), 'graph_workflows', ['tenant_id'], unique=False)

    # Workflow Instances table
    op.create_table('workflow_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['graph_workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_instances_tenant_id'), 'workflow_instances', ['tenant_id'], unique=False)

    # Workflow Checkpoints table
    op.create_table('workflow_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('node_id', sa.Text(), nullable=True),
        sa.Column('state_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['workflow_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_checkpoints_tenant_id'), 'workflow_checkpoints', ['tenant_id'], unique=False)

    # Human Review Sessions table
    op.create_table('human_review_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('node_id', sa.Text(), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['workflow_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_human_review_sessions_tenant_id'), 'human_review_sessions', ['tenant_id'], unique=False)

    # Audit Log table
    op.create_table('audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actor', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.Text(), nullable=True),
        sa.Column('resource', sa.Text(), nullable=True),
        sa.Column('decision', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_tenant_id'), 'audit_log', ['tenant_id'], unique=False)


def downgrade():
    """Remove all tables"""
    op.drop_table('audit_log')
    op.drop_table('human_review_sessions')
    op.drop_table('workflow_checkpoints')
    op.drop_table('workflow_instances')
    op.drop_table('graph_workflows')
    op.drop_table('crews')
    op.drop_table('agents')
