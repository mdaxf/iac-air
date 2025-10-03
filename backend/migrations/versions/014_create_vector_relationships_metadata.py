"""Create vector relationships metadata

Revision ID: 014
Revises: 013
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector_relationship_metadata table
    op.create_table('vector_relationship_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('source_table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_table_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(), nullable=False),  # 'foreign_key', 'inferred', 'manual'
        sa.Column('cardinality', sa.String(), nullable=True),  # '1:1', '1:N', 'N:M'
        sa.Column('description', sa.Text(), nullable=True),

        # Join condition (JSONB)
        # {
        #   "source_columns": ["customer_id"],
        #   "target_columns": ["id"],
        #   "join_type": "INNER",
        #   "condition": "customers.customer_id = orders.customer_id"
        # }
        sa.Column('join_condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Business metadata (JSONB)
        # {
        #   "relationship_name": "customer_orders",
        #   "business_description": "Links customers to their orders"
        # }
        sa.Column('business_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Usage statistics
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),

        # Confidence score for inferred relationships (0.0 to 1.0)
        sa.Column('confidence_score', sa.Float(), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_table_id'], ['vector_table_metadata.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_table_id'], ['vector_table_metadata.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('ix_vector_relationship_metadata_db_alias', 'vector_relationship_metadata', ['db_alias'])
    op.create_index('ix_vector_relationship_metadata_source_table', 'vector_relationship_metadata', ['source_table_id'])
    op.create_index('ix_vector_relationship_metadata_target_table', 'vector_relationship_metadata', ['target_table_id'])
    op.create_index('ix_vector_relationship_metadata_type', 'vector_relationship_metadata', ['relationship_type'])
    op.create_index('ix_vector_relationship_metadata_usage_count', 'vector_relationship_metadata', ['usage_count'])

    # Create unique constraint on source_table + target_table
    op.create_index('uq_vector_relationship_metadata_source_target', 'vector_relationship_metadata',
                    ['source_table_id', 'target_table_id'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_vector_relationship_metadata_source_target', table_name='vector_relationship_metadata')
    op.drop_index('ix_vector_relationship_metadata_usage_count', table_name='vector_relationship_metadata')
    op.drop_index('ix_vector_relationship_metadata_type', table_name='vector_relationship_metadata')
    op.drop_index('ix_vector_relationship_metadata_target_table', table_name='vector_relationship_metadata')
    op.drop_index('ix_vector_relationship_metadata_source_table', table_name='vector_relationship_metadata')
    op.drop_index('ix_vector_relationship_metadata_db_alias', table_name='vector_relationship_metadata')
    op.drop_table('vector_relationship_metadata')
