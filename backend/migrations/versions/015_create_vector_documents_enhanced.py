"""Create enhanced vector documents table

Revision ID: 015
Revises: 014
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vector_documents_enhanced table
    op.create_table('vector_documents_enhanced',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('db_alias', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),  # 'table', 'column', 'relationship', 'entity', 'metric', 'template', 'uploaded_file'
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),  # FK to related metadata table

        # Content
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=True),  # For deduplication

        # Chunking information
        sa.Column('chunk_index', sa.Integer(), nullable=True),  # For multi-chunk documents
        sa.Column('total_chunks', sa.Integer(), nullable=True),
        sa.Column('parent_document_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Vector embedding
        sa.Column('embedding', Vector(1536), nullable=True),

        # Metadata (JSONB)
        # {
        #   "source": "schema_sync",
        #   "file_name": "database_documentation.pdf",
        #   "page_number": 5,
        #   "section": "Customer Tables",
        #   "keywords": ["customer", "order", "revenue"],
        #   "language": "en"
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status tracking
        sa.Column('status', sa.String(), server_default='pending', nullable=False),  # 'pending', 'processing', 'ready', 'failed'
        sa.Column('error_message', sa.Text(), nullable=True),

        # Quality metrics
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),

        # Usage statistics
        sa.Column('retrieval_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_retrieved_at', sa.DateTime(timezone=True), nullable=True),

        # Audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_document_id'], ['vector_documents_enhanced.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('ix_vector_documents_enhanced_db_alias', 'vector_documents_enhanced', ['db_alias'])
    op.create_index('ix_vector_documents_enhanced_document_type', 'vector_documents_enhanced', ['document_type'])
    op.create_index('ix_vector_documents_enhanced_reference_id', 'vector_documents_enhanced', ['reference_id'])
    op.create_index('ix_vector_documents_enhanced_status', 'vector_documents_enhanced', ['status'])
    op.create_index('ix_vector_documents_enhanced_content_hash', 'vector_documents_enhanced', ['content_hash'])
    op.create_index('ix_vector_documents_enhanced_parent_id', 'vector_documents_enhanced', ['parent_document_id'])
    op.create_index('ix_vector_documents_enhanced_retrieval_count', 'vector_documents_enhanced', ['retrieval_count'])

    # Create vector index for similarity search
    op.execute('CREATE INDEX ix_vector_documents_enhanced_embedding ON vector_documents_enhanced USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    op.drop_index('ix_vector_documents_enhanced_embedding', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_retrieval_count', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_parent_id', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_content_hash', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_status', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_reference_id', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_document_type', table_name='vector_documents_enhanced')
    op.drop_index('ix_vector_documents_enhanced_db_alias', table_name='vector_documents_enhanced')
    op.drop_table('vector_documents_enhanced')
