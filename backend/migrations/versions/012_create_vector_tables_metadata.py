"""Create vector tables metadata

Revision ID: 012
Revises: 011
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector_table_metadata table
    op.create_table('vector_table_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('schema_name', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('table_type', sa.String(), nullable=True),  # 'BASE TABLE', 'VIEW', 'MATERIALIZED VIEW'
        sa.Column('description', sa.Text(), nullable=True),

        # Business metadata (JSONB)
        # {
        #   "display_name": "Customer Orders",
        #   "category": "sales",
        #   "tags": ["important", "pii"],
        #   "business_owner": "sales_team",
        #   "update_frequency": "hourly",
        #   "row_count_estimate": 1000000,
        #   "size_mb": 450.5
        # }
        sa.Column('business_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Technical metadata (JSONB)
        # {
        #   "primary_key": ["customer_id", "order_id"],
        #   "indexes": [...],
        #   "partitioned": true,
        #   "compression": "zstd"
        # }
        sa.Column('technical_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Sample queries (JSONB array)
        sa.Column('sample_queries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Vector embedding for semantic search
        sa.Column('embedding', Vector(1536), nullable=True),

        # Usage statistics
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),

        # Quality score (0.0 to 1.0)
        sa.Column('quality_score', sa.Float(), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_schema_sync', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_vector_table_metadata_db_alias', 'vector_table_metadata', ['db_alias'])
    op.create_index('ix_vector_table_metadata_schema_name', 'vector_table_metadata', ['schema_name'])
    op.create_index('ix_vector_table_metadata_table_name', 'vector_table_metadata', ['table_name'])
    op.create_index('ix_vector_table_metadata_table_type', 'vector_table_metadata', ['table_type'])
    op.create_index('ix_vector_table_metadata_usage_count', 'vector_table_metadata', ['usage_count'])
    op.create_index('ix_vector_table_metadata_last_used_at', 'vector_table_metadata', ['last_used_at'])

    # Create unique constraint on db_alias + schema + table
    op.create_index('uq_vector_table_metadata_db_schema_table', 'vector_table_metadata',
                    ['db_alias', 'schema_name', 'table_name'], unique=True)

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_vector_table_metadata_embedding ON vector_table_metadata USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_index('ix_vector_table_metadata_embedding', table_name='vector_table_metadata')
    op.drop_index('uq_vector_table_metadata_db_schema_table', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_last_used_at', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_usage_count', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_table_type', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_table_name', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_schema_name', table_name='vector_table_metadata')
    op.drop_index('ix_vector_table_metadata_db_alias', table_name='vector_table_metadata')
    op.drop_table('vector_table_metadata')
