"""Add user management tables and update existing tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '63d953b31627'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new column `db_alias` to conversations table
    op.add_column('conversations', sa.Column('db_alias', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the column if we downgrade
    op.drop_column('conversations', 'db_alias')