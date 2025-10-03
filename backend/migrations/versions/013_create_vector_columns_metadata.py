"""Create vector columns metadata

Revision ID: 013
Revises: 012
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector_column_metadata table
    op.create_table('vector_column_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('table_metadata_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('column_name', sa.String(), nullable=False),
        sa.Column('data_type', sa.String(), nullable=False),
        sa.Column('is_nullable', sa.Boolean(), nullable=True),
        sa.Column('column_description', sa.Text(), nullable=True),

        # Business metadata (JSONB)
        # {
        #   "display_name": "Customer ID",
        #   "business_definition": "Unique identifier for customer",
        #   "data_classification": "PII",
        #   "format": "UUID",
        #   "examples": ["550e8400-e29b-41d4-a716-446655440000"],
        #   "value_range": {"min": 0, "max": 999999},
        #   "allowed_values": ["active", "inactive", "pending"]
        # }
        sa.Column('business_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Statistics (JSONB)
        # {
        #   "distinct_count": 50000,
        #   "null_count": 0,
        #   "min_value": "2020-01-01",
        #   "max_value": "2024-12-31",
        #   "avg_length": 36,
        #   "top_values": [{"value": "active", "count": 30000}]
        # }
        sa.Column('statistics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Vector embedding for semantic search
        sa.Column('embedding', Vector(1536), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['table_metadata_id'], ['vector_table_metadata.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('ix_vector_column_metadata_table_id', 'vector_column_metadata', ['table_metadata_id'])
    op.create_index('ix_vector_column_metadata_column_name', 'vector_column_metadata', ['column_name'])
    op.create_index('ix_vector_column_metadata_data_type', 'vector_column_metadata', ['data_type'])

    # Create unique constraint on table_metadata_id + column_name
    op.create_index('uq_vector_column_metadata_table_column', 'vector_column_metadata',
                    ['table_metadata_id', 'column_name'], unique=True)

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_vector_column_metadata_embedding ON vector_column_metadata USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_index('ix_vector_column_metadata_embedding', table_name='vector_column_metadata')
    op.drop_index('uq_vector_column_metadata_table_column', table_name='vector_column_metadata')
    op.drop_index('ix_vector_column_metadata_data_type', table_name='vector_column_metadata')
    op.drop_index('ix_vector_column_metadata_column_name', table_name='vector_column_metadata')
    op.drop_index('ix_vector_column_metadata_table_id', table_name='vector_column_metadata')
    op.drop_table('vector_column_metadata')
