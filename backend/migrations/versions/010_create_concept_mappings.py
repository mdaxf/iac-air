"""Create concept mappings table

Revision ID: 010
Revises: 009
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create concept_mappings table
    op.create_table('concept_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('canonical_term', sa.String(), nullable=False),  # e.g., "customer"
        sa.Column('synonyms', postgresql.ARRAY(sa.String()), nullable=True),  # e.g., ["client", "account", "buyer"]

        # What this concept maps to
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK to business_entities
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK to business_metrics
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK to query_templates (created next)

        # Optional context for disambiguation
        sa.Column('context', sa.Text(), nullable=True),
        # e.g., "Used in sales contexts. In finance reports, use 'account' instead."

        # Category for grouping
        sa.Column('category', sa.String(), nullable=True),  # e.g., "financial", "temporal", "geographic"

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entity_id'], ['business_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['metric_id'], ['business_metrics.id'], ondelete='CASCADE')
        # template_id FK will be added after query_templates table is created
    )

    # Create indexes
    op.create_index('ix_concept_mappings_db_alias', 'concept_mappings', ['db_alias'])
    op.create_index('ix_concept_mappings_canonical_term', 'concept_mappings', ['canonical_term'])
    op.create_index('ix_concept_mappings_entity_id', 'concept_mappings', ['entity_id'])
    op.create_index('ix_concept_mappings_metric_id', 'concept_mappings', ['metric_id'])
    op.create_index('ix_concept_mappings_category', 'concept_mappings', ['category'])

    # Create GIN index on synonyms array for fast searches
    op.execute('CREATE INDEX ix_concept_mappings_synonyms ON concept_mappings USING GIN (synonyms)')

    # Create unique constraint on db_alias + canonical_term
    op.create_index('uq_concept_mappings_db_alias_canonical', 'concept_mappings',
                    ['db_alias', 'canonical_term'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_concept_mappings_db_alias_canonical', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_synonyms', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_category', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_metric_id', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_entity_id', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_canonical_term', table_name='concept_mappings')
    op.drop_index('ix_concept_mappings_db_alias', table_name='concept_mappings')
    op.drop_table('concept_mappings')
