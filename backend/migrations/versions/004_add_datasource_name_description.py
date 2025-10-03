"""Add name and description fields to report_datasources

Revision ID: 004_add_datasource_name_description
Revises: 003_add_api_history
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003_add_api_history'
branch_labels = None
depends_on = None


def upgrade():
    # Add name and description columns to report_datasources table
    op.add_column('report_datasources', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('report_datasources', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    # Remove name and description columns from report_datasources table
    op.drop_column('report_datasources', 'description')
    op.drop_column('report_datasources', 'name')