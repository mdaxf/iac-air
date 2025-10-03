"""Create business metrics table

Revision ID: 009
Revises: 008
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create business_metrics table
    op.create_table('business_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK to business_entities

        # Metric definition stored as JSONB
        sa.Column('metric_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "display_name": "Revenue",
        #   "description": "Total sales revenue excluding returns and discounts",
        #   "business_formula": "SUM(Order Amount) - SUM(Returns) - SUM(Discounts)",
        #   "sql_template": "SELECT ... FROM ... WHERE ...",
        #   "parameters": [
        #     {"name": "start_date", "type": "date", "required": true},
        #     ...
        #   ],
        #   "dimensions": ["region", "time", "product_category"],
        #   "aggregation_type": "sum",
        #   "unit": "USD",
        #   "refresh_frequency": "hourly",
        #   "business_rules": ["Exclude cancelled orders", ...],
        #   "min_value": 0,
        #   "max_value": null
        # }

        # Vector embedding for semantic search
        sa.Column('embedding', Vector(1536), nullable=True),

        # Usage statistics
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('success_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('failure_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_by', sa.String(), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entity_id'], ['business_entities.id'], ondelete='SET NULL')
    )

    # Create indexes
    op.create_index('ix_business_metrics_db_alias', 'business_metrics', ['db_alias'])
    op.create_index('ix_business_metrics_metric_name', 'business_metrics', ['metric_name'])
    op.create_index('ix_business_metrics_entity_id', 'business_metrics', ['entity_id'])
    op.create_index('ix_business_metrics_last_used_at', 'business_metrics', ['last_used_at'])

    # Create unique constraint on db_alias + metric_name
    op.create_index('uq_business_metrics_db_alias_metric_name', 'business_metrics',
                    ['db_alias', 'metric_name'], unique=True)

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_business_metrics_embedding ON business_metrics USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_index('ix_business_metrics_embedding', table_name='business_metrics')
    op.drop_index('uq_business_metrics_db_alias_metric_name', table_name='business_metrics')
    op.drop_index('ix_business_metrics_last_used_at', table_name='business_metrics')
    op.drop_index('ix_business_metrics_entity_id', table_name='business_metrics')
    op.drop_index('ix_business_metrics_metric_name', table_name='business_metrics')
    op.drop_index('ix_business_metrics_db_alias', table_name='business_metrics')
    op.drop_table('business_metrics')
