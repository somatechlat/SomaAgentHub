"""Add tenant_id to all models for multi-tenancy support

Revision ID: add_multi_tenancy
Revises: 
Create Date: 2025-12-03

BREAKING CHANGE: All tables now require tenant_id for isolation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_multi_tenancy'
down_revision = None  # Update this if there are existing migrations
branch_labels = None
depends_on = None


def upgrade():
    """Add tenant_id columns to all existing tables"""
    
    # Add tenant_id to agents table
    op.add_column('agents', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)
    
    # Add tenant_id to crews table
    op.add_column('crews', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_crews_tenant_id'), 'crews', ['tenant_id'], unique=False)
    
    # Add tenant_id to graph_workflows table
    op.add_column('graph_workflows', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_graph_workflows_tenant_id'), 'graph_workflows', ['tenant_id'], unique=False)
    
    # Add tenant_id to workflow_instances table
    op.add_column('workflow_instances', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_workflow_instances_tenant_id'), 'workflow_instances', ['tenant_id'], unique=False)
    
    # Add tenant_id to workflow_checkpoints table
    op.add_column('workflow_checkpoints', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_workflow_checkpoints_tenant_id'), 'workflow_checkpoints', ['tenant_id'], unique=False)
    
    # Add tenant_id to human_review_sessions table
    op.add_column('human_review_sessions', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_human_review_sessions_tenant_id'), 'human_review_sessions', ['tenant_id'], unique=False)
    
    # Add tenant_id to audit_log table
    op.add_column('audit_log', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_audit_log_tenant_id'), 'audit_log', ['tenant_id'], unique=False)
    
    # Backfill tenant_id with a default tenant UUID for existing data
    default_tenant_id = str(uuid.uuid4())
    
    op.execute(f"""
        UPDATE agents SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE crews SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE graph_workflows SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE workflow_instances SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE workflow_checkpoints SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE human_review_sessions SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
        UPDATE audit_log SET tenant_id = '{default_tenant_id}' WHERE tenant_id IS NULL;
    """)
    
    # Make tenant_id NOT NULL after backfill
    op.alter_column('agents', 'tenant_id', nullable=False)
    op.alter_column('crews', 'tenant_id', nullable=False)
    op.alter_column('graph_workflows', 'tenant_id', nullable=False)
    op.alter_column('workflow_instances', 'tenant_id', nullable=False)
    op.alter_column('workflow_checkpoints', 'tenant_id', nullable=False)
    op.alter_column('human_review_sessions', 'tenant_id', nullable=False)
    op.alter_column('audit_log', 'tenant_id', nullable=False)


def downgrade():
    """Remove tenant_id columns (DESTRUCTIVE - will lose tenant isolation)"""
    
    # Drop indexes
    op.drop_index(op.f('ix_audit_log_tenant_id'), table_name='audit_log')
    op.drop_index(op.f('ix_human_review_sessions_tenant_id'), table_name='human_review_sessions')
    op.drop_index(op.f('ix_workflow_checkpoints_tenant_id'), table_name='workflow_checkpoints')
    op.drop_index(op.f('ix_workflow_instances_tenant_id'), table_name='workflow_instances')
    op.drop_index(op.f('ix_graph_workflows_tenant_id'), table_name='graph_workflows')
    op.drop_index(op.f('ix_crews_tenant_id'), table_name='crews')
    op.drop_index(op.f('ix_agents_tenant_id'), table_name='agents')
    
    # Drop columns
    op.drop_column('audit_log', 'tenant_id')
    op.drop_column('human_review_sessions', 'tenant_id')
    op.drop_column('workflow_checkpoints', 'tenant_id')
    op.drop_column('workflow_instances', 'tenant_id')
    op.drop_column('graph_workflows', 'tenant_id')
    op.drop_column('crews', 'tenant_id')
    op.drop_column('agents', 'tenant_id')
