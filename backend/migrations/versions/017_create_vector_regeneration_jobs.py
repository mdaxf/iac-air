"""Create vector regeneration jobs table

Revision ID: 017
Revises: 016
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector_regeneration_jobs table
    op.create_table('vector_regeneration_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),  # 'full_sync', 'incremental', 'single_table', 'single_entity', 'bulk_regenerate'
        sa.Column('db_alias', sa.String(), nullable=True),  # NULL for cross-database jobs
        sa.Column('target_type', sa.String(), nullable=True),  # 'table', 'column', 'relationship', 'entity', 'metric', 'template', 'document'
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),  # Specific item to process

        # Job parameters (JSONB)
        # {
        #   "schema_names": ["public", "analytics"],
        #   "table_names": ["customers", "orders"],
        #   "force_refresh": true,
        #   "generate_embeddings": true,
        #   "batch_size": 100
        # }
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status tracking
        sa.Column('status', sa.String(), server_default='pending', nullable=False),  # 'pending', 'running', 'completed', 'failed', 'cancelled'
        sa.Column('progress', sa.Float(), server_default='0.0', nullable=True),  # 0.0 to 1.0
        sa.Column('current_step', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Results (JSONB)
        # {
        #   "tables_synced": 150,
        #   "columns_synced": 2000,
        #   "relationships_discovered": 45,
        #   "embeddings_generated": 2195,
        #   "errors": []
        # }
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timing
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_vector_regeneration_jobs_job_type', 'vector_regeneration_jobs', ['job_type'])
    op.create_index('ix_vector_regeneration_jobs_db_alias', 'vector_regeneration_jobs', ['db_alias'])
    op.create_index('ix_vector_regeneration_jobs_status', 'vector_regeneration_jobs', ['status'])
    op.create_index('ix_vector_regeneration_jobs_target_type', 'vector_regeneration_jobs', ['target_type'])
    op.create_index('ix_vector_regeneration_jobs_target_id', 'vector_regeneration_jobs', ['target_id'])
    op.create_index('ix_vector_regeneration_jobs_created_at', 'vector_regeneration_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_vector_regeneration_jobs_created_at', table_name='vector_regeneration_jobs')
    op.drop_index('ix_vector_regeneration_jobs_target_id', table_name='vector_regeneration_jobs')
    op.drop_index('ix_vector_regeneration_jobs_target_type', table_name='vector_regeneration_jobs')
    op.drop_index('ix_vector_regeneration_jobs_status', table_name='vector_regeneration_jobs')
    op.drop_index('ix_vector_regeneration_jobs_db_alias', table_name='vector_regeneration_jobs')
    op.drop_index('ix_vector_regeneration_jobs_job_type', table_name='vector_regeneration_jobs')
    op.drop_table('vector_regeneration_jobs')
