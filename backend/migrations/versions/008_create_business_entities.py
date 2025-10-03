"""Create business entities table

Revision ID: 008
Revises: 7407468662e5
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '7407468662e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create business_entities table
    op.create_table('business_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('entity_name', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=True),  # 'dimension', 'fact', 'metric'
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('business_owner', sa.String(), nullable=True),

        # Semantic attributes stored as JSONB
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "display_name": "Customer",
        #   "plural_name": "Customers",
        #   "synonyms": ["client", "account", "buyer"],
        #   "business_domain": "sales",
        #   "sensitivity_level": "pii",
        #   "common_questions": ["How many customers?", ...]
        # }

        # Source mapping stored as JSONB
        sa.Column('source_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "primary_table": "public.customers",
        #   "related_tables": [
        #     {"table": "public.customer_addresses", "relationship": "1:N", "join_key": "customer_id"},
        #     ...
        #   ],
        #   "denormalized_view": "analytics.dim_customer",
        #   "key_columns": ["customer_id", "email", "created_at"]
        # }

        # Metrics associated with this entity
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: [
        #   {
        #     "name": "Total Customers",
        #     "calculation": "COUNT(DISTINCT customer_id)",
        #     "description": "Total number of unique customers"
        #   },
        #   ...
        # ]

        # Vector embedding for semantic search
        sa.Column('embedding', Vector(1536), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_business_entities_db_alias', 'business_entities', ['db_alias'])
    op.create_index('ix_business_entities_entity_name', 'business_entities', ['entity_name'])
    op.create_index('ix_business_entities_entity_type', 'business_entities', ['entity_type'])

    # Create unique constraint on db_alias + entity_name
    op.create_index('uq_business_entities_db_alias_entity_name', 'business_entities',
                    ['db_alias', 'entity_name'], unique=True)

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_business_entities_embedding ON business_entities USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_index('ix_business_entities_embedding', table_name='business_entities')
    op.drop_index('uq_business_entities_db_alias_entity_name', table_name='business_entities')
    op.drop_index('ix_business_entities_entity_type', table_name='business_entities')
    op.drop_index('ix_business_entities_entity_name', table_name='business_entities')
    op.drop_index('ix_business_entities_db_alias', table_name='business_entities')
    op.drop_table('business_entities')
