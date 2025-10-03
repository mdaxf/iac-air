"""Create query templates table

Revision ID: 011
Revises: 010
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create query_templates table
    op.create_table('query_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=True),  # NULL means applies to all databases
        sa.Column('template_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),  # e.g., "analytics", "finance", "sales"

        # Example questions that match this template
        sa.Column('example_questions', postgresql.ARRAY(sa.Text()), nullable=True),
        # e.g., ["Show me revenue by region", "What is total revenue?"]

        # SQL template with parameter placeholders
        sa.Column('sql_template', sa.Text(), nullable=False),
        # e.g., "SELECT {dimension_field}, SUM(revenue) FROM ... GROUP BY {dimension_field}"

        # Template parameters configuration
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: [
        #   {
        #     "name": "dimension_field",
        #     "type": "select",
        #     "required": true,
        #     "default": "region",
        #     "options": ["region", "country", "state"]
        #   },
        #   ...
        # ]

        # Required entities and metrics for this template
        sa.Column('required_entities', postgresql.ARRAY(sa.String()), nullable=True),  # ["Customer", "Order"]
        sa.Column('required_metrics', postgresql.ARRAY(sa.String()), nullable=True),  # ["Revenue", "CLV"]

        # Vector embedding for semantic search
        sa.Column('embedding', Vector(1536), nullable=True),

        # Usage statistics
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('success_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_by', sa.String(), nullable=True),

        # Status
        sa.Column('status', sa.String(), server_default='active', nullable=True),  # active, draft, archived

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_query_templates_db_alias', 'query_templates', ['db_alias'])
    op.create_index('ix_query_templates_template_name', 'query_templates', ['template_name'])
    op.create_index('ix_query_templates_category', 'query_templates', ['category'])
    op.create_index('ix_query_templates_status', 'query_templates', ['status'])
    op.create_index('ix_query_templates_usage_count', 'query_templates', ['usage_count'])
    op.create_index('ix_query_templates_last_used_at', 'query_templates', ['last_used_at'])

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_query_templates_embedding ON query_templates USING ivfflat (embedding vector_cosine_ops)')

    # Now add the FK constraint to concept_mappings for template_id
    op.create_foreign_key(
        'fk_concept_mappings_template_id',
        'concept_mappings',
        'query_templates',
        ['template_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop FK constraint from concept_mappings first
    op.drop_constraint('fk_concept_mappings_template_id', 'concept_mappings', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_query_templates_embedding', table_name='query_templates')
    op.drop_index('ix_query_templates_last_used_at', table_name='query_templates')
    op.drop_index('ix_query_templates_usage_count', table_name='query_templates')
    op.drop_index('ix_query_templates_status', table_name='query_templates')
    op.drop_index('ix_query_templates_category', table_name='query_templates')
    op.drop_index('ix_query_templates_template_name', table_name='query_templates')
    op.drop_index('ix_query_templates_db_alias', table_name='query_templates')

    # Drop table
    op.drop_table('query_templates')
