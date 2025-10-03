"""Add auto_execute_query field to conversations

Revision ID: 005_add_auto_execute_query
Revises: 004_add_datasource_name_description
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add auto_execute_query column to conversations table
    op.add_column('conversations', sa.Column('auto_execute_query', sa.Boolean(), nullable=False, default=True, server_default='true'))


def downgrade():
    # Remove auto_execute_query column from conversations table
    op.drop_column('conversations', 'auto_execute_query')