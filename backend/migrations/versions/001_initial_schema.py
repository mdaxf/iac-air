"""Initial schema with vector documents, database connections, and chat

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create database_connections table
    op.create_table('database_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('host', sa.String(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('schema_whitelist', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_blacklist', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_connections_alias'), 'database_connections', ['alias'], unique=True)
    op.create_index(op.f('ix_database_connections_id'), 'database_connections', ['id'], unique=False)

    # Create vector_documents table
    op.create_table('vector_documents',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vector_documents_db_alias'), 'vector_documents', ['db_alias'], unique=False)
    op.create_index(op.f('ix_vector_documents_resource_id'), 'vector_documents', ['resource_id'], unique=False)
    op.create_index(op.f('ix_vector_documents_resource_type'), 'vector_documents', ['resource_type'], unique=False)
    op.create_index(op.f('ix_vector_documents_tenant_id'), 'vector_documents', ['tenant_id'], unique=False)

    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('sql_query', sa.Text(), nullable=True),
        sa.Column('result_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chart_meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('db_alias', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_conversation_id'), 'chat_messages', ['conversation_id'], unique=False)

    # Create vector index for similarity search (using ivfflat initially)
    op.execute('''
        CREATE INDEX idx_vector_documents_embedding
        ON vector_documents
        USING ivfflat (embedding vector_l2_ops)
        WITH (lists = 100)
    ''')


def downgrade() -> None:
    # Drop vector index first
    op.execute('DROP INDEX IF EXISTS idx_vector_documents_embedding')

    # Drop tables in reverse order
    op.drop_index(op.f('ix_chat_messages_conversation_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_index(op.f('ix_vector_documents_tenant_id'), table_name='vector_documents')
    op.drop_index(op.f('ix_vector_documents_resource_type'), table_name='vector_documents')
    op.drop_index(op.f('ix_vector_documents_resource_id'), table_name='vector_documents')
    op.drop_index(op.f('ix_vector_documents_db_alias'), table_name='vector_documents')
    op.drop_table('vector_documents')
    op.drop_index(op.f('ix_database_connections_id'), table_name='database_connections')
    op.drop_index(op.f('ix_database_connections_alias'), table_name='database_connections')
    op.drop_table('database_connections')