"""Add API call history table

Revision ID: 003_add_api_history
Revises: 002_add_user_management
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_api_history'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_call_history table
    op.create_table('api_call_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('method', sa.String(10), nullable=False, index=True),
        sa.Column('path', sa.String(500), nullable=False, index=True),
        sa.Column('full_url', sa.String(1000), nullable=False),
        sa.Column('query_params', postgresql.JSON(), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=True, index=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('referer', sa.String(500), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('username', sa.String(50), nullable=True, index=True),
        sa.Column('is_admin', sa.String(10), nullable=True),
        sa.Column('request_headers', postgresql.JSON(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('request_size', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False, index=True),
        sa.Column('response_headers', postgresql.JSON(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=True, index=True),
        sa.Column('endpoint_name', sa.String(100), nullable=True, index=True),
        sa.Column('api_version', sa.String(10), nullable=True),
        sa.Column('source', sa.String(50), nullable=True, index=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('correlation_id', sa.String(100), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for performance
    op.create_index('idx_api_history_date_status', 'api_call_history', ['created_at', 'status_code'])
    op.create_index('idx_api_history_user_date', 'api_call_history', ['user_id', 'created_at'])
    op.create_index('idx_api_history_method_path', 'api_call_history', ['method', 'path'])
    op.create_index('idx_api_history_duration', 'api_call_history', ['duration_ms'])
    op.create_index('idx_api_history_source_date', 'api_call_history', ['source', 'created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_api_history_source_date', table_name='api_call_history')
    op.drop_index('idx_api_history_duration', table_name='api_call_history')
    op.drop_index('idx_api_history_method_path', table_name='api_call_history')
    op.drop_index('idx_api_history_user_date', table_name='api_call_history')
    op.drop_index('idx_api_history_date_status', table_name='api_call_history')

    # Drop table
    op.drop_table('api_call_history')